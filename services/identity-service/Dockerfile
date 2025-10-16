# Use a specific, minimal Python base image
FROM python:3.11.6-slim-bookworm

# Set environment variables for a secure and efficient build
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_DISABLE_PIP_VERSION_CHECK=on \
	PIP_NO_CACHE_DIR=on \
	PYTHONPATH=/app

WORKDIR /app

# Install dependencies
COPY services/identity-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser
COPY services/common /app/services/common
COPY common /app/common
COPY clickhouse_driver /app/clickhouse_driver
COPY services/identity-service/ /app/
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

EXPOSE 10002

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10002"]
