FROM python:3.13-slim

WORKDIR /app

COPY services/billing-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/billing-service/app/ ./app/
COPY . .

EXPOSE 1010

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
