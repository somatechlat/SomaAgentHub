import os
from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from services.common.config.base_settings import resolve_env

GATEWAY_URL = resolve_env("GATEWAY_URL", "http://gateway-api:8000")
STATIC_TOKEN = resolve_env("SOMAGENT_AIRFLOW_JWT") or resolve_env(
    "SOMAGENT_BEARER_TOKEN"
)


def _build_token() -> str:
    if not STATIC_TOKEN:
        raise RuntimeError(
            "Missing bearer token. Set SOMAGENT_AIRFLOW_JWT (or SOMAGENT_BEARER_TOKEN)."
        )
    return STATIC_TOKEN


def trigger_memory_refresh(**context):
    campaign = context.get("params", {}).get("campaign_name", "default")
    url = f"{GATEWAY_URL}/api/memory/refresh"
    payload = {"campaign": campaign, "force": True}
    headers = {
        "Authorization": f"Bearer {_build_token()}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="memory_refresh",
    default_args=default_args,
    description="Refresh memory gateway embeddings for a campaign",
    schedule_interval="0 * * * *",  # hourly
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:
    refresh = PythonOperator(
        task_id="refresh_campaign_memory",
        python_callable=trigger_memory_refresh,
        provide_context=True,
        params={"campaign_name": "fall_launch"},
    )

    refresh
