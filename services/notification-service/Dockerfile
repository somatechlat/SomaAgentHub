FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on

WORKDIR /app

COPY services/notification-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    adduser --disabled-password --gecos "app" --home /home/app app && \
    chown -R app:app /app

COPY services/notification-service/app/ ./services/notification-service/app/

USER app

EXPOSE 10026

ENV PORT=10026
CMD ["sh", "-c", "uvicorn services.notification-service.app.main:app --host 0.0.0.0 --port ${PORT:-10026}"]
