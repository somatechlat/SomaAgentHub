FROM python:3.13-slim

# Install build dependencies for packages requiring compilation (gcc, python headers, and build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY . .

EXPOSE 1009

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
