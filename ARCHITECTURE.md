# HIBACore — Architecture Deep Dive

> This document is aimed at contributors and technical reviewers. For a general overview, see [README.md](README.md).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
3. [Request Lifecycle](#request-lifecycle)
4. [RAG Pipeline](#rag-pipeline)
5. [Semantic Memory](#semantic-memory)
6. [Skill Engine](#skill-engine)
7. [DeepAgents](#deepagents)
8. [Async Worker System](#async-worker-system)
9. [Multi-Tenancy Model](#multi-tenancy-model)
10. [Frontend Architecture](#frontend-architecture)
11. [Infrastructure](#infrastructure)
12. [Security Model](#security-model)

---

## System Overview

HIBACore is composed of three independently deployable services that communicate over HTTP and Azure Service Bus:

```
┌──────────────────────────────────────────────────────────────────┐
│  [Frontend]  React 18 + Vite + TypeScript                       │
│              Hosted: Azure Static Web Apps                       │
│              Auth: MSAL (Azure AD Bearer Token)                 │
└───────────────────────────┬──────────────────────────────────────┘
                            │ REST + SSE
                            │ Headers: Authorization, X-Tenant-Id
┌───────────────────────────▼──────────────────────────────────────┐
│  [Backend]   FastAPI — Python 3.12                              │
│              Hosted: Azure App Service (Gunicorn + Uvicorn)     │
│              Middleware pipeline (CORS → Tenant → Rate → Safety)│
└────────────────┬──────────────┬────────────────┬────────────────┘
                 │              │                │
           Azure OpenAI   Azure Search    Azure Service Bus
           Cosmos DB       pgvector         (async workers)
           Redis            Key Vault
                            App Config
┌───────────────────────────▼──────────────────────────────────────┐
│  [Skill Engine]  Node.js + Express                              │
│              Hosted: Azure Container Instance                   │
│              Protocol: OpenAI function-calling format           │
│              Hot-loadable skill registry                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### App Factory Pattern

`app/main.py` implements an app factory (`create_app()`). This separates concerns cleanly and makes testing straightforward — you can call `create_app()` with different configurations.

### Middleware Stack

Middleware is registered in **reverse order** in FastAPI (last added = first executed). Execution order at runtime:

```
CORS → CorrelationId → Tenant → RateLimit → ContentSafety → SecurityHeaders
```

| Middleware | Responsibility |
|---|---|
| `CORSMiddleware` | Configures allowed origins from `CORS_ORIGINS` env |
| `CorrelationIdMiddleware` | Injects a `X-Correlation-Id` on every request for distributed tracing |
| `TenantMiddleware` | Extracts `tenant_id` from JWT `tid` claim or `X-Tenant-Id` header; stores it in `ContextVar` |
| `RateLimitMiddleware` | Redis-backed sliding window rate limit per tenant |
| `ContentSafetyMiddleware` | Calls Azure Content Safety on message body before routing |
| `SecurityHeadersMiddleware` | Adds HSTS, CSP, X-Frame-Options, X-Content-Type-Options |

### Router Map

| Prefix | Module | Description |
|---|---|---|
| `/api/v1/chat` | `chat.py` | Chat messages + SSE streaming |
| `/api/v1/conversations` | `conversations.py` | Conversation history CRUD |
| `/api/v1/documents` | `documents.py` | Document upload + listing |
| `/api/v1/agents` | `agents.py` | DeepAgent (Azure AI Projects) |
| `/api/v1/agent` | `agent.py` | ZeroClaw external agent gateway |
| `/api/v1/admin` | `admin.py` | Tenant admin operations |
| `/api/v1/admin/super` | `admin_super.py` | Platform-level management |
| `/api/v1/notifications` | `notifications.py` | Push notification endpoints |
| `/api/v1/webhooks` | `webhooks.py` | Incoming webhook receiver |
| `/health` | `health.py` | Health check (k8s/App Service probes) |

---

## Request Lifecycle

### Standard Chat (SSE Streaming)

```
Client → POST /api/v1/chat/message
  ↓
TenantMiddleware extracts tenant_id from JWT
  ↓
RateLimitMiddleware checks Redis sliding window
  ↓
ContentSafetyMiddleware screens message
  ↓
chat.py handler:
  1. Load conversation history from Cosmos DB
  2. Query pgvector for semantically similar past messages (top-k)
  3. If Citation=ON: call Azure AI Search hybrid retrieval
  4. Assemble system prompt + context + history
  5. Stream response from Azure OpenAI (GPT-4o-mini or GPT-4o)
  6. Yield SSE events: token deltas + citation chunks
  7. Publish to Service Bus: memory-vectorize, summarize, entity-extract
```

### Deep Thinking (Synchronous)

```
Client → POST /api/v1/chat/deep
  ↓ (same middleware stack)
chat.py deep handler:
  1. Fetch Skill Engine tool index → GET http://skill-engine:3000/skills/index
  2. Build LangGraph state machine via agents/builder.py
  3. Execute reasoning loop (Planning → Tool calls → Final answer)
  4. Return full response with:
     - content: final answer
     - reasoning: full thinking trace
     - artifacts: code blocks / structured text panels
```

---

## RAG Pipeline

```
Document Upload
  ↓
Blob Storage (Azure Storage Account)
  ↓
Service Bus: document-ingestion queue
  ↓
Worker: call Azure Document Intelligence (OCR + layout)
  ↓
Semantic chunking: 512 tokens, 64-token overlap
  ↓
Generate embeddings: text-embedding-3-small (Azure OpenAI)
  ↓
Index into Azure AI Search (vector + text fields)

─────────────────────────────────────────────

Query Time (Citation=ON)
  ↓
Generate query embedding
  ↓
Azure AI Search: hybrid search (vector + BM25)
  ↓
RRF (Reciprocal Rank Fusion) merge
  ↓
Cross-encoder reranker (engine/rag/reranker.py)
  ↓
Top-k chunks injected into system prompt
  ↓
Citations extracted and returned to frontend (engine/rag/citations.py)
```

---

## Semantic Memory

Long-term memory gives the model access to relevant messages from previous sessions.

**Database schema** (`message_embeddings` table):

```sql
CREATE TABLE message_embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   TEXT NOT NULL,
    session_id  TEXT NOT NULL,
    message_id  TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR(1536),
    timestamp   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON message_embeddings
    USING ivfflat (embedding vector_cosine_ops);
```

**Indexing**: every sent/received message triggers `memory-vectorize` queue → worker generates embedding and upserts into PostgreSQL.

**Retrieval**: before each query, cosine similarity search (`<=>` operator) filtered by `tenant_id` returns the `top_k` most relevant past messages.

---

## Skill Engine

The Skill Engine is a standalone Node.js/Express microservice that acts as a plugin registry for the deep-thinking LangGraph agent.

**Protocol**: skills are exposed in OpenAI function-calling format (`GET /skills/index` returns an array of tool definitions). The LangGraph agent pre-binds them to the LLM via `llm.bind_tools(tools)`.

**Adding a skill**: create a folder in `backend/skill-engine/registry/<skill-name>/` containing:

```
registry/
  my-skill/
    skill.json      ← metadata: name, description, input, entrypoint
    index.js        ← exports an async function(payload) => result
```

`skill.json` format:
```json
{
  "name": "my-skill",
  "description": "What this skill does, shown to the LLM",
  "input": "{ query: string }",
  "entrypoint": "index.js"
}
```

Skills are loaded at startup; the registry is scanned from the filesystem. Rate limiting (100 req/15min) is enforced per endpoint.

---

## DeepAgents

Two agent implementations exist in HIBACore:

### 1. LangGraph Agent (`agents/builder.py`)

Used by the Skill Engine for deep-thinking chat mode:

```
State: AgentState { messages, tasks, current_task, workspace_files }

Graph:
  [entry] → agent (call_model)
                ↓ has tool_calls?
               yes → action (ToolNode) → agent (loop)
                no → END
```

Tools available: everything registered in the Skill Engine.

### 2. Azure AI Projects Agent (`services/agents/agent_loop.py`)

Used by the `/api/v1/agents` endpoints for fully autonomous runs:

- Creates an ephemeral agent per tenant on Azure AI Foundry
- Attaches `CodeInterpreterTool` and `FileSearchTool`
- Opens a thread, injects the user query
- Streams progress via Azure AI Projects SDK `create_and_stream_run`
- Maps SDK events to our SSE format (`thread.message.delta` → `content`, `thread.run.step.delta` → `status`)

---

## Async Worker System

Service Bus queues decouple real-time request handling from heavy background work:

| Queue | Worker | Trigger |
|---|---|---|
| `document-ingestion` | Document parser | After file upload |
| `memory-vectorize` | pgvector indexer | After every chat message |
| `summarize` | Session summarizer | Periodically / on session end |
| `entity-extract` | Gremlin entity extractor | After every chat message |
| `persona` | Persona modeler | After session activity |
| `recommendations` | Recommendation generator | After session activity |
| `reflection` | Reflection agent | After session end |

Each publish function in `services/messaging/bus.py` is silently skipped if `AZURE_SERVICE_BUS_FQDN` is not configured (useful for local dev).

---

## Multi-Tenancy Model

Tenant isolation is enforced at every layer:

**Identity flow**:
```
Request → TenantMiddleware
  → Extract from JWT claim "tid" (priority 1)
  → Extract from header X-Tenant-Id (priority 2, if APIM-validated)
  → Store in ContextVar (available globally without passing through functions)
```

**Data isolation**:
- **Cosmos DB**: partition key = `tenant_id`
- **pgvector**: all queries include `WHERE tenant_id = %s`
- **Azure AI Search**: filter expression `tenant_id eq '<id>'`
- **App Configuration**: labels map to `tenant_id` for per-tenant settings

**Configuration**: `ConfigManager` loads tenant-specific overrides from Azure App Configuration at request time — allowing different AI models, rate limits, and feature flags per tenant.

---

## Frontend Architecture

```
src/
├── components/
│   ├── ChatInput.tsx       ← model selector, file upload, Thinking/Citation toggles
│   ├── MessageBubble.tsx   ← markdown render, reasoning trace, citations, artifact button
│   ├── ChatContainer.tsx   ← SSE stream handler, Zustand integration, Quick Actions
│   └── Sidebar.tsx         ← navigation, conversation history, user profile
├── pages/
│   ├── Chat.tsx
│   ├── Admin.tsx
│   └── SuperAdmin.tsx
├── services/
│   └── api.ts              ← unified API client: auto-injects Authorization + X-Tenant-Id
├── store/
│   └── authStore.ts        ← Zustand: tenant, session, auth state
└── App.tsx
```

**Streaming**: `ChatContainer` uses `EventSource` (SSE) for `fast` and `normal` model tiers. For `deep` tier, it falls back to a standard `fetch` call that waits for the full reasoning response.

---

## Infrastructure

Terraform definitions in `terraform/` target Azure with the following resources:

| Resource | Type | Purpose |
|---|---|---|
| App Service Plan | B1 | Hosts backend App Service |
| App Service | — | FastAPI backend |
| Static Web App | — | React frontend |
| Azure OpenAI | S0 | LLM and embedding models |
| Cosmos DB | Serverless | Chat history |
| PostgreSQL Flexible Server | Standard_B1ms | pgvector memory |
| Azure AI Search | — | Document retrieval |
| Container Instance | 1vCPU / 1GB | Skill Engine |
| Service Bus | — | Async worker queues |
| Key Vault | — | Secrets management |
| App Configuration | — | Per-tenant settings |
| Container Registry | Basic | Docker image storage |
| Storage Account | Standard_LRS | Document blob storage |
| Application Insights | — | Telemetry |
| Log Analytics Workspace | — | Centralized logs |
| Virtual Network | — | Private connectivity |

---

## Security Model

| Concern | Implementation |
|---|---|
| Authentication | Azure AD / Entra ID — MSAL on frontend, JWT validation on backend |
| Authorization | JWT `tid` claim drives tenant isolation; no cross-tenant data access possible |
| Secrets | Zero hardcoded credentials; all secrets in Azure Key Vault |
| Managed Identity | `DefaultAzureCredential` for all Azure SDK calls — no service principal keys in code |
| Rate limiting | Redis sliding window per tenant via `RateLimitMiddleware` |
| Content moderation | Azure Content Safety screens every inbound message |
| Transport | HTTPS enforced; HSTS header set by `SecurityHeadersMiddleware` |
| Input validation | Pydantic v2 on all request models |
| CORS | Explicit allow-list; no wildcard origins in production |
