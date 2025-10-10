FROM python:3.13-slim

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

USER app

EXPOSE 1004

ENV PORT=1004 WORKERS=1
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-1004} --workers ${WORKERS:-1}"]
