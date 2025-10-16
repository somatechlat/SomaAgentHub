"""Airflow DAG for scheduling SomaAgentHub session warmups."""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG

from plugins.soma_temporal import SomaGatewayTemporalOperator

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="soma_session_warmup",
    description="Warm up SomaAgentHub session workflows via the public gateway.",
    schedule_interval="@hourly",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["somagent", "temporal"],
) as dag:
    SomaGatewayTemporalOperator(
        task_id="trigger_demo_session",
        prompt="Daily autonomous health check",
        tenant="demo",
        user="airflow-service",
        capsule_id="system-health-check",
        metadata={"source": "airflow", "workflow": "session_warmup"},
    )
