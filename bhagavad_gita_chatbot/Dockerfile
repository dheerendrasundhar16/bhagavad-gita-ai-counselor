# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Bhagavad Gita AI Counselor (Backend)
#
# Builds the FastAPI backend. The Streamlit frontend is deployed separately
# on Streamlit Community Cloud (free) and connects via BACKEND_URL.
#
# Build:  docker build -t gita-counselor-backend .
# Run:    docker run -e GEMINI_API_KEY=xxx -p 8000:8000 gita-counselor-backend
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source (exclude data/chromadb — mounted at runtime)
COPY api/         ./api/
COPY chains/      ./chains/
COPY services/    ./services/
COPY utils/       ./utils/
COPY vectorstore/ ./vectorstore/

# Pre-create data directories (ChromaDB will initialize here)
RUN mkdir -p data/chromadb data/uploads logs

# Env defaults (override at runtime)
ENV HOST=0.0.0.0
ENV PORT=8000
ENV CHROMA_DB_PATH=./data/chromadb
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Health-check — polls /status every 30 seconds
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/status || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
