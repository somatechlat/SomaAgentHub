FROM python:3.11-slim

WORKDIR /app

COPY services/token-estimator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/token-estimator/app/ ./app/

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
