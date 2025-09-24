FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml /app/

RUN pip install --upgrade pip && \
    pip install hatchling

# Dependencies are installed per-service using hatch inside entrypoint scripts.

CMD ["python", "-m", "http.server", "8000"]
