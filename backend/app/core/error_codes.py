"""
Task 2.03 — Error Codes Catalog (Dizionario Centralizzato)

Ogni errore del sistema è mappato qui: codice → (HTTP status, messaggio, categoria).
Mai usare stringhe libere per gli errori. Sempre ErrorCode.XXX.
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple


class ErrorInfo(NamedTuple):
    """Immutable info per ogni codice errore."""
    http_status: int
    default_message: str
    category: str


class ErrorCode(Enum):
    """Catalogo centralizzato di tutti i codici errore del sistema.

    Formato: CATEGORIA_NNN
    - AUTH: autenticazione / autorizzazione
    - TENANT: multi-tenancy
    - AI: motore AI / LLM
    - RAG: retrieval augmented generation
    - MEM: memory (Cosmos, pgvector, graph)
    - TOOL: agent tools
    - UPLOAD: upload documenti
    - VOICE: pipeline vocale
    - INFRA: infrastruttura
    """

    # ── AUTH ──────────────────────────────────────────────────
    AUTH_001 = ErrorInfo(401, "Token JWT mancante.", "Authentication")
    AUTH_002 = ErrorInfo(401, "Token JWT scaduto.", "Authentication")
    AUTH_003 = ErrorInfo(403, "Audience o Issuer non valido.", "Authentication")
    AUTH_004 = ErrorInfo(403, "Scope insufficiente per questa operazione.", "Authorization")

    # ── TENANT ───────────────────────────────────────────────
    TENANT_101 = ErrorInfo(403, "Tenant ID mancante nel context.", "Tenant Isolation")
    TENANT_102 = ErrorInfo(403, "Accesso cross-tenant rilevato e bloccato.", "Tenant Isolation")
    TENANT_103 = ErrorInfo(429, "Rate limit per-tenant superato.", "Rate Limiting")
    TENANT_104 = ErrorInfo(404, "Tenant non trovato.", "Tenant Management")

    # ── AI ENGINE ────────────────────────────────────────────
    AI_201 = ErrorInfo(503, "Servizio AI temporaneamente non disponibile.", "AI Engine")
    AI_202 = ErrorInfo(429, "Rate limit del provider AI superato.", "AI Engine")
    AI_203 = ErrorInfo(503, "Failover fallito su tutti i provider AI.", "AI Engine")
    AI_204 = ErrorInfo(400, "Rilevata potenziale prompt injection.", "AI Security")
    AI_205 = ErrorInfo(400, "Contesto troppo lungo per il modello selezionato.", "AI Engine")
    AI_206 = ErrorInfo(422, "Risposta del modello vuota o malformata.", "AI Engine")

    # ── RAG ───────────────────────────────────────────────────
    RAG_301 = ErrorInfo(422, "Formato documento non supportato.", "RAG Pipeline")
    RAG_302 = ErrorInfo(422, "Documento troppo grande (max 100MB).", "RAG Pipeline")
    RAG_303 = ErrorInfo(500, "Parsing del documento fallito.", "RAG Pipeline")
    RAG_304 = ErrorInfo(500, "Generazione embedding fallita.", "RAG Pipeline")
    RAG_305 = ErrorInfo(500, "Indicizzazione AI Search fallita.", "RAG Pipeline")

    # ── MEMORY ────────────────────────────────────────────────
    MEM_401 = ErrorInfo(503, "Database chat non raggiungibile.", "Memory")
    MEM_402 = ErrorInfo(503, "Vector database non raggiungibile.", "Memory")
    MEM_403 = ErrorInfo(500, "Operazione Knowledge Graph fallita.", "Memory")

    # ── TOOLS ─────────────────────────────────────────────────
    TOOL_501 = ErrorInfo(403, "Tool non autorizzato per questo tenant.", "Agent Tools")
    TOOL_502 = ErrorInfo(500, "Esecuzione sandbox fallita.", "Agent Tools")
    TOOL_503 = ErrorInfo(408, "Tool timeout superato (>30s).", "Agent Tools")
    TOOL_504 = ErrorInfo(422, "Argomenti tool non validi.", "Agent Tools")

    # ── UPLOAD ────────────────────────────────────────────────
    UPLOAD_601 = ErrorInfo(422, "Tipo file non supportato.", "Upload")
    UPLOAD_602 = ErrorInfo(422, "Malware rilevato nel file.", "Upload")
    UPLOAD_603 = ErrorInfo(413, "File troppo grande.", "Upload")

    # ── VOICE ─────────────────────────────────────────────────
    VOICE_701 = ErrorInfo(503, "Servizio STT non disponibile.", "Voice")
    VOICE_702 = ErrorInfo(503, "Servizio TTS non disponibile.", "Voice")
    VOICE_703 = ErrorInfo(408, "WebRTC connection timeout.", "Voice")

    # ── INFRA ─────────────────────────────────────────────────
    INFRA_901 = ErrorInfo(500, "Key Vault non raggiungibile.", "Infrastructure")
    INFRA_902 = ErrorInfo(500, "Service Bus non disponibile.", "Infrastructure")
    INFRA_903 = ErrorInfo(500, "Servizio di telemetria non disponibile.", "Infrastructure")

    # ── POLICY ENGINE ──────────────────────────────────────────
    POLICY_001 = ErrorInfo(403, "Il tuo account è sospeso. Contatta il supporto.", "Policy Security")
    POLICY_002 = ErrorInfo(403, "Questa funzione non è attiva per il tuo account.", "Policy Permission")
    POLICY_003 = ErrorInfo(403, "Questa funzione non è disponibile nel tuo piano.", "Policy Plan")
    POLICY_004 = ErrorInfo(202, "Azione in attesa di approvazione del tuo amministratore.", "Policy Workflow")
    POLICY_005 = ErrorInfo(403, "Limite thinking level raggiunto per il tuo piano.", "Policy Limit")
    POLICY_006 = ErrorInfo(403, "URL di destinazione non autorizzato.", "Network Security")

    @property
    def http_status(self) -> int:
        """HTTP status code associato a questo errore."""
        return self.value.http_status

    @property
    def default_message(self) -> str:
        """Messaggio di default user-friendly."""
        return self.value.default_message

    @property
    def category(self) -> str:
        """Categoria dell'errore (per dashboard/filtering)."""
        return self.value.category
