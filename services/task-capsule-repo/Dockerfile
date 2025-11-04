FROM python:3.13-slim

WORKDIR /app

COPY services/task-capsule-repo/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/task-capsule-repo/app/ ./app/
# Copy any additional source files from the service directory (excluding the Dockerfile itself)
COPY services/task-capsule-repo/ ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
