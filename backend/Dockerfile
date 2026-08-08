# ===========================================================================
# AI Disaster Relief Coordination Platform — Dockerfile
# ===========================================================================
# Multi-stage build for a minimal, production-ready image.
# Stage 1: Build dependencies
# Stage 2: Runtime image (slim)
# ===========================================================================

# ---------------------------------------------------------------------------
# Stage 1 — Builder
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install all Python dependencies into a prefix directory
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---------------------------------------------------------------------------
# Stage 2 — Runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Non-root user for security
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Ensure the SQLite database directory is writable by the non-root user
RUN mkdir -p /app/data && chown -R appuser:appgroup /app

USER appuser

# ---------------------------------------------------------------------------
# Environment defaults (overridden by docker-compose or K8s secrets)
# ---------------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    DATABASE_URL=sqlite:////app/data/disaster_relief.db

EXPOSE 8000

# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info"]
