# Use the official Airflow image, pinned to a specific version
FROM apache/airflow:2.9.0-python3.11

# Switch to root to create directories and set permissions
USER root
RUN mkdir -p /opt/airflow/airflow_logging /opt/airflow/dags /opt/airflow/plugins && \
    chown -R airflow:airflow /opt/airflow

# Switch to the airflow user for installations and operations
USER airflow

# Install Python dependencies as the correct user
RUN pip install --no-cache-dir --user \
	python-logging-loki \
	requests \
	pyjwt \
	prometheus-client \
	apache-airflow-providers-http \
	apache-airflow-providers-redis \
	apache-airflow-providers-postgres

# Copy application code
COPY --chown=airflow:airflow airflow_logging /opt/airflow/airflow_logging
COPY --chown=airflow:airflow dags /opt/airflow/dags
COPY --chown=airflow:airflow plugins /opt/airflow/plugins

# Set environment variable for logging configuration
ENV AIRFLOW__LOGGING__LOGGING_CONFIG_CLASS=airflow_logging.loki_config.LOGGING_CONFIG