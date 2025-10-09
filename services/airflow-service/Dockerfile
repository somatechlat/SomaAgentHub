FROM apache/airflow:2.9.0-python3.11
USER root
RUN pip install --no-cache-dir python-logging-loki requests
USER airflow
COPY airflow_logging /opt/airflow/airflow_logging
COPY dags /opt/airflow/dags
ENV AIRFLOW__LOGGING__LOGGING_CONFIG_CLASS=airflow_logging.loki_config.LOGGING_CONFIG