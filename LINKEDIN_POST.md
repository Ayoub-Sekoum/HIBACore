# LinkedIn Post — HIBACore Launch

> Copy-paste ready. Adjust the GitHub link before posting.
> Recommended: attach 2-3 images from the `/docs/linkedin/` folder.

---

## Post Text

---

I've been building something for the past few months, and today I'm open-sourcing it.

**HIBACore** — a multi-tenant enterprise AI chatbot platform, now on GitHub.

This is alpha software. It's not polished, some edges are rough, and I'm still figuring out parts of it. But the core is real, and I think it's worth sharing.

---

**What it does:**

The platform lets multiple organizations run isolated AI chat environments from a single deployment. Each tenant gets separate chat history, document indexes, and memory — nothing leaks between them.

Three model tiers:
- Fast mode (GPT-4o Mini) — streaming, low latency
- Standard mode (GPT-4o) — balanced
- Deep mode (O1/reasoning) — full thinking trace, returns artifacts

Document RAG with hybrid search (vector + BM25), cross-encoder reranking, and semantic chunking. Long-term memory via pgvector — the model can reference conversations from weeks ago.

An extensible Skill Engine (Node.js microservice) exposes plugins to the LangGraph reasoning loop in OpenAI function-calling format. Drop a folder in the registry to add a new capability.

Async workers on Azure Service Bus handle document ingestion, memory vectorization, entity extraction, session summarization, and persona modeling — all decoupled from the real-time request path.

---

**Stack:**
Python 3.12 · FastAPI · LangGraph · Azure OpenAI · pgvector · Azure AI Search · Cosmos DB · React 18 · TypeScript · Zustand · MSAL · Docker

---

**What's next:**

- Voice interface (Azure AI Voice — currently disabled, SDK not yet stable)
- Better local dev story (Ollama air-gapped mode is partially implemented)
- Proper test coverage
- UI polish

---

If you're working on enterprise AI infrastructure, multi-tenant SaaS, or RAG systems — I'd genuinely like to hear what you think.

Link in comments.

---

**GitHub:** https://github.com/Ayoub-Sekoum/HIBACore

---

## Hashtags (pick 6-8, don't pile them all)

#OpenSource #ArtificialIntelligence #FastAPI #React #AzureOpenAI #LLM #RAG #EnterpriseAI #Python #TypeScript #SoftwareEngineering #MachineLearning #ChatGPT #LangChain #MultiTenant

---

## Comment (post separately to keep the main post clean)

GitHub repo: https://github.com/Ayoub-Sekoum/HIBACore

Architecture details and setup guide in the README and ARCHITECTURE.md.
Contributions welcome — it's alpha, so there's plenty to improve.

---

## Notes on posting

- Post as **a document / article** rather than a plain status update if you want more reach
- First comment = GitHub link (LinkedIn suppresses reach for posts with external links in the body)
- Tag 2-3 people you'd genuinely want feedback from
- Best posting times: Tuesday–Thursday, 8–10am or 5–7pm your local time
- Don't edit the post in the first 30 minutes after publishing (hurts the algorithm)
