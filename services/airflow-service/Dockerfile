FROM apache/airflow:2.9.0-python3.11

USER root

# Install additional runtime dependencies used by our DAGs/operators.
RUN pip install --no-cache-dir \
	python-logging-loki \
	requests \
	pyjwt \
	prometheus-client \
	apache-airflow-providers-http \
	apache-airflow-providers-redis \
	apache-airflow-providers-postgres

USER airflow

COPY airflow_logging /opt/airflow/airflow_logging
COPY dags /opt/airflow/dags
COPY plugins /opt/airflow/plugins

ENV AIRFLOW__LOGGING__LOGGING_CONFIG_CLASS=airflow_logging.loki_config.LOGGING_CONFIG