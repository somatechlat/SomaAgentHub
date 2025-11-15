FROM python:3.13-slim

WORKDIR /app

COPY services/constitution-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/constitution-service/app/ ./app/
COPY services/constitution-service/ .

EXPOSE 1008

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
