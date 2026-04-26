# Python 3.14 slim image for Django + Celery
FROM python:3.14-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/ ./requirements/
RUN pip install --no-cache-dir --user -r requirements/base.txt

# --- Production stage ---
FROM python:3.14-slim-bookworm AS production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x docker/entrypoint.sh

# Create non-root user (security best practice)
RUN groupadd -r appgroup && useradd -r -g appgroup appuser \
    && mkdir -p /app/staticfiles /app/media /app/backups \
    && chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
