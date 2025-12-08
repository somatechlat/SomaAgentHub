# Use a specific, minimal Python base image
FROM python:3.11.6-slim-bookworm

# Production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on \
    PYTHONPATH=/app \
    HOST=0.0.0.0

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libpq-dev \
    gcc \
    g++ \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (assuming a requirements.txt exists or creating a minimal one)
# For now, we'll try to use the one if it exists, or install common libs
COPY services/workflow-engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Copy application code
COPY services/common /app/services/common
COPY common /app/common
COPY services/workflow-engine/app/ /app/app/

# Set proper permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check endpoint (Workers might not expose HTTP, but Temporal client check is good)
# For a worker, we might check if the process is running or use a specific health endpoint if implemented
# Assuming standard Temporal worker pattern
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "app.main" || exit 1

# Production startup
CMD ["python", "-m", "app.main"]
