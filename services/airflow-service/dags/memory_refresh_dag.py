from datetime import datetime, timedelta
import os
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway-api:8000")


def trigger_memory_refresh(**context):
    campaign = context.get("params", {}).get("campaign_name", "default")
    url = f"{GATEWAY_URL}/api/memory/refresh"
    payload = {"campaign": campaign, "force": True}
    resp = requests.post(url, json=payload, timeout=10)
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
