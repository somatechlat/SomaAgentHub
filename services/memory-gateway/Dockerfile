FROM python:3.13-slim

WORKDIR /app

COPY services/memory-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/memory-gateway/app/ ./app/
COPY services/memory-gateway/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
