# ==============================================================================
# PAYGUARD Backend — Production Dockerfile
# ==============================================================================
# Multi-stage optimized build using Python 3.11 Slim with non-root security.
# ==============================================================================

FROM python:3.11-slim AS builder

WORKDIR /build

# Install compilation tools needed for C-extensions (cryptography, scikit-learn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into wheels
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# ------------------------------------------------------------------------------
# Production Runtime Stage
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Install runtime dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group
RUN groupadd -g 10001 payguard && \
    useradd -u 10001 -g payguard -s /bin/bash -m payguard

WORKDIR /app

# Install wheels from builder
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Copy application code
COPY app /app/backend/app

# Create persistent storage directory for SQLite database
RUN mkdir -p /app/data && \
    chown -R payguard:payguard /app

# Switch to non-root user
USER payguard

# Set environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_PATH=/app/data/payguard.db

WORKDIR /app/backend

EXPOSE 8000

# Health check probe against API health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

