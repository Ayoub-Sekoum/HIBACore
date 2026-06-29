"""
Task 2.01 — Pydantic v2 Error Schema + APIResponse Model

Ogni endpoint restituisce SEMPRE APIResponse.
Mai dict, mai modelli diretti, mai risposte non strutturate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Dettaglio errore standardizzato.

    Restituito nel campo `error` di APIResponse quando success=False.
    Mai esporre stack trace, path di file, o query SQL.
    """

    error_code: str = Field(
        ...,
        description="Codice errore dal catalogo centralizzato (es. AI_201)",
        examples=["AI_201", "TENANT_101"],
    )
    message: str = Field(
        ...,
        description="Messaggio user-friendly, mai dettagli interni",
        examples=["Servizio AI temporaneamente non disponibile."],
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="UUID v4 univoco per questa richiesta (per tracciamento)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp UTC dell'errore",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error_code": "AI_201",
                    "message": "Servizio AI temporaneamente non disponibile.",
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2026-03-12T10:30:00Z",
                }
            ]
        }
    }


class APIResponse(BaseModel, Generic[T]):
    """Response wrapper standard per tutti gli endpoint.

    Esempio successo:
        {"success": true, "data": {...}, "error": null}

    Esempio errore:
        {"success": false, "data": null, "error": {"error_code": "AI_201", ...}}
    """

    success: bool = Field(
        ...,
        description="True se la richiesta è andata a buon fine",
    )
    data: T | None = Field(
        default=None,
        description="Payload della risposta (null in caso di errore)",
    )
    error: ErrorDetail | None = Field(
        default=None,
        description="Dettaglio errore (null in caso di successo)",
    )

    @classmethod
    def ok(cls, data: Any = None) -> APIResponse:
        """Factory per risposta di successo."""
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(
        cls,
        error_code: str,
        message: str,
        request_id: str | None = None,
    ) -> APIResponse:
        """Factory per risposta di errore."""
        return cls(
            success=False,
            data=None,
            error=ErrorDetail(
                error_code=error_code,
                message=message,
                request_id=request_id or str(uuid4()),
            ),
        )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": {"message": "Ciao!"},
                    "error": None,
                },
                {
                    "success": False,
                    "data": None,
                    "error": {
                        "error_code": "AI_201",
                        "message": "Servizio AI temporaneamente non disponibile.",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2026-03-12T10:30:00Z",
                    },
                },
            ]
        }
    }
