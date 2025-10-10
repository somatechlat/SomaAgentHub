FROM python:3.13-slim

# Environment hardening
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_DISABLE_PIP_VERSION_CHECK=on \
	PIP_NO_CACHE_DIR=off

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
	adduser --disabled-password --gecos "app" --home /home/app app && \
	chown -R app:app /app

COPY app/ ./app/
COPY . .

# Run as non-root
USER app

EXPOSE 8000

# Honour PORT env if provided; default 8000
ENV PORT=8000 WORKERS=1
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-1}"]
