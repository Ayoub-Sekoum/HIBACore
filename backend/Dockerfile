# Task 10.01: Docker Multi-stage Build (Backend)
# Build stage
FROM python:3.12-slim as builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Run stage
FROM python:3.12-slim

# Crea un utente non root per sicurezza
RUN adduser --disabled-password --gecos "" appuser && \
    apt-get update && apt-get install -y --no-install-recommends libmagic1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*

COPY . .

# Ensure appuser owns the directory
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
