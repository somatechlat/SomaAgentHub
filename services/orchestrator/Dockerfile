# Use a specific, minimal Python base image
FROM python:3.11.6-slim-bookworm

# Production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on \
    PYTHONPATH=/app \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install system dependencies for PostgreSQL, Redis, and security tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libpq-dev \
    gcc \
    g++ \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY services/orchestrator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Copy application code
COPY services/common /app/services/common
COPY common /app/common
COPY services/orchestrator/app/ /app/app/

# Set proper permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get(f'http://localhost:{PORT}/health/live')"

# Expose port
EXPOSE 8000

# Production startup with proper configuration
CMD ["python", "-m", "app.main"]
