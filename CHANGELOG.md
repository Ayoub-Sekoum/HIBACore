# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.5] - 2026-07-07

### Added
- **Core Governance & Policy Manager**: Introduced role-based SuperAdmin and TenantAdmin dashboards along with a real-time policy guard middleware (`policy_guard.py`) supporting live audit logs and Server-Sent Event (SSE) notifications for compliance updates.
- **Autonomous DeepAgents Integration**: Added the `AgentOrchestrator` wrapping the Azure AI Projects SDK, enabling multi-step planning, autonomous tool utilization (including sandboxed Code Interpreter and File Search), and streaming progress updates.
- **Dynamic Memory Backend**: Seamlessly integrated a pgvector-based PostgreSQL long-term memory backend alongside Cosmos DB.
- **Bilingual Capabilities**: Enhanced locale-aware UI structures and automated translations on key layouts.

### Fixed
- **MSAL Auth & CORS Issues**: Resolved severe browser-level popup blockages and Cross-Origin-Opener-Policy (COOP) errors by migrating authentication from `loginPopup` to `loginRedirect` with robust async MSAL v3 initialization. Included proper COOP and COEP security headers on the server.
- **Azure App Service Startup Bottlenecks**:
  - Eliminated the Oryx compilation timeouts by moving PyTorch/sentence-transformers to CPU-only wheels inside `requirements.txt`.
  - Fixed virtualenv path issues under Linux Azure environment by explicitly activating the `antenv` sandbox and resolving relative paths inside `startup.sh`.
  - Excluded root path `/` from tenant verification middleware and added a root health handler to prevent Azure Deployment CLI status timeouts (404 errors).
- **AttributeError**: Corrected missing configurations mapping `AZURE_OPENAI_DEPLOYMENT_NAME` to `AZURE_OPENAI_NORMAL_DEPLOYMENT` in deep agent orchestration modules.
- **PowerShell Zip Packaging**: Fixed Linux directory structure compression issues on Windows by utilizing native `tar` instead of `Compress-Archive` to retain proper UNIX slash mappings.

---

## [0.2.0] - 2026-06-15

### Added
- **Cost-Optimization Scheduling**: Created custom PowerShell automation scripts (`suspend-resources.ps1`, `hoba_start.ps1`, `hoba_stop.ps1`) to gracefully suspend/resume App Service, PostgreSQL Flexible Server, and ZeroClaw agent instances, reducing monthly operating costs on Azure.
- **Prompt Injection & AI Security Layer**: Implemented strict inbound message sanitization, regex detection patterns, and active Azure AI Content Safety middleware integration.
- **Canvas Interface**: Developed a split-pane Canvas frontend feature that renders side-by-side rich artifacts (source code codeblocks, HTML pages, SVG vector mockups, and charts) directly beside the chat workspace.

---

## [0.1.0-alpha] - 2026-05-05

### Added
- **Initial Public Open Source Release** under `HIBACore`.
- **Multi-Tenant Foundation**: Implemented `TenantMiddleware` utilizing Python `ContextVars` to dynamically partition Cosmos DB, pgvector, and Azure AI Search configurations based on Microsoft Entra ID claims.
- **Core Chat Stack**: Established FastAPI REST backend structure, custom SSE ReadableStream frontend client reader, and integrated Azure OpenAI configurations.
- **Skill Engine**: Drop-in Node.js hot-loadable microservice supporting custom tool schemas mapped directly into the model function-calling pipeline.
- **Infrastructure-as-Code**: Modular Terraform blueprints supporting Azure Container App, KeyVault, Cosmos, and OpenAI resource provisioning.
