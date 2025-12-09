FROM python:3.11.6-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/memory-gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Copy Service Code (Monorepo Structure)
COPY services/common /app/services/common
COPY services/memory-gateway /app/services/memory_gateway

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "services.memory_gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
