# Use a specific, minimal Python base image
FROM python:3.11.6-slim-bookworm

# Set environment variables for a secure and efficient build
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_DISABLE_PIP_VERSION_CHECK=on \
	PIP_NO_CACHE_DIR=on \
	PYTHONPATH=/app

WORKDIR /app

# Install kubectl for Volcano job submissions
RUN apt-get update \
	&& apt-get install -y --no-install-recommends ca-certificates curl \
	&& curl -fsSLo /usr/local/bin/kubectl "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
	&& chmod +x /usr/local/bin/kubectl \
	&& apt-get purge -y curl \
	&& apt-get autoremove -y \
	&& rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY services/orchestrator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser
COPY services/common /app/services/common
COPY common /app/common
COPY services/orchestrator/ /app/
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

EXPOSE 10001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10001"]
