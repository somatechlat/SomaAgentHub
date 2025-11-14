FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

COPY app /app/app

EXPOSE {{SERVICE_PORT}}

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{{SERVICE_PORT}}"]
