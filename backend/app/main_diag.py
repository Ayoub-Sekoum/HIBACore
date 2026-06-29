"""
HOBA Backend — Versione diagnostica minimale.
Usata temporaneamente per isolare crash di startup.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="HOBA AI - Diagnostic", version="1.0.0-diag")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "diagnostic",
        "env": os.environ.get("ENVIRONMENT", "unknown"),
        "openai_configured": bool(os.environ.get("AZURE_OPENAI_API_KEY")),
    }

@app.get("/ready")
async def ready():
    return {"status": "ready"}
