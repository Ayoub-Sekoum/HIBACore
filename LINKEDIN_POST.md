# LinkedIn Post - HIBACore Release (v0.3.5)

*Note: This post is strictly based on the technical facts and architecture documented in the project Wiki.*

---

**[ENG Version]**

🚀 **I'm thrilled to announce the open-source release of HIBACore (v0.3.5)!** 

Based on our internal HOBA AI Enterprise project, HIBACore is a full-stack, enterprise-grade AI Chatbot architecture built from the ground up to support Multi-Tenancy, strict data isolation, and Azure-native integrations. 

Instead of just gluing APIs together, we tackled real production challenges:

🧠 **Architecture & Stack:**
- **Backend:** Python (FastAPI) deployed on Azure App Services (Linux).
- **Frontend:** React & TypeScript SPA with strict COOP/COEP security headers.
- **Database:** PostgreSQL Flexible Server with `pgvector` for Long-Term Semantic Memory.
- **AI Core:** Azure OpenAI (`gpt-4o-mini`) + RAG pipeline.
- **Agents:** ZeroClaw Agent executing securely inside Azure Container Instances.

🛠️ **Engineering Highlights from our Wiki:**
- **Enterprise Auth:** Integrated `@azure/msal-react` with Microsoft Entra ID. We migrated to a robust `loginRedirect` flow with async MSAL v3 initialization to bypass modern browser COOP popup blockers.
- **Infrastructure as Code:** Full Terraform deployment plan (`infrastructure/terraform`) available in the repo for ACA, Cosmos, KeyVault, and OpenAI modules.
- **Cost Optimization:** Built dynamic PowerShell automation to gracefully suspend/resume all backend, frontend, database, and container instances outside business hours, significantly cutting Azure costs.
- **Build Optimization:** Overcame PyTorch build timeouts on Oryx by forcing CPU-only wheels for our `sentence-transformers` reranker.

The repository is now public and includes our complete `ARCHITECTURE.md` and Infrastructure setup. 

🔗 **Check out the repo here:** https://github.com/Ayoub-Sekoum/HIBACore

We are currently in Alpha. Feedback, PRs, and architectural discussions are welcome! 

#AI #Azure #FastAPI #React #Terraform #OpenSource #SoftwareEngineering #PgVector #MicrosoftEntra

---

**[ITA Version]**

🚀 **Sono felice di annunciare il rilascio open-source di HIBACore (v0.3.5)!**

Nato dal progetto interno HOBA AI Enterprise, HIBACore è un'architettura AI full-stack pensata per il mondo enterprise, progettata per supportare Multi-Tenancy, isolamento dei dati e integrazione nativa con Azure.

Non ci siamo limitati a collegare due API, ma abbiamo affrontato sfide reali di produzione:

🧠 **Architettura e Stack:**
- **Backend:** Python (FastAPI) distribuito su Azure App Service.
- **Frontend:** React & TypeScript SPA.
- **Database:** PostgreSQL Flexible Server con `pgvector` per la Memoria Semantica a lungo termine.
- **AI Core:** Azure OpenAI (`gpt-4o-mini`) con pipeline RAG integrata.
- **Agenti:** ZeroClaw Agent eseguito in sicurezza tramite Azure Container Instances.

🛠️ **Sfide ingegneristiche risolte (dalla nostra Wiki):**
- **Autenticazione Enterprise:** Integrazione `@azure/msal-react` con Microsoft Entra ID. Abbiamo migrato il flusso a `loginRedirect` gestendo l'inizializzazione asincrona di MSAL v3 per superare i blocchi dei popup legati alle policy COOP dei browser moderni.
- **Infrastructure as Code:** L'intero piano di deploy Terraform è disponibile nella repository.
- **Ottimizzazione Costi:** Sviluppata automazione PowerShell dinamica per sospendere e riavviare App Service, DB e Container fuori dall'orario di lavoro, abbattendo drasticamente i costi su Azure.
- **Ottimizzazione Build:** Risolto il timeout di compilazione su Oryx forzando i pacchetti CPU-only di PyTorch per il nostro modello di reranking.

La repository è pubblica e include l'intera documentazione architetturale e infrastrutturale.

🔗 **Link alla Repo:** https://github.com/Ayoub-Sekoum/HIBACore

Siamo in fase Alpha. Feedback e PR sono benvenuti!

#AI #Azure #FastAPI #React #Terraform #OpenSource #SoftwareEngineering #PgVector #MicrosoftEntra
