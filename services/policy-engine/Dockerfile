FROM python:3.13-slim

WORKDIR /app

COPY services/policy-engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/policy-engine/app/ ./app/
COPY services/policy-engine/ .

EXPOSE 10020

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10020", "--workers", "1"]
