from datetime import datetime, timedelta
import os
import time

import jwt
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway-api:8000")
GATEWAY_SECRET = os.getenv("SOMAGENT_GATEWAY_JWT_SECRET")
STATIC_TOKEN = os.getenv("SOMAGENT_AIRFLOW_JWT")


def _build_token() -> str:
    if STATIC_TOKEN:
        return STATIC_TOKEN
    if not GATEWAY_SECRET:
        raise RuntimeError("SOMAGENT_GATEWAY_JWT_SECRET environment variable not provided for Airflow")
    now = int(time.time())
    payload = {
        "iss": "airflow",
        "sub": os.getenv("SOMAGENT_AIRFLOW_SUBJECT", "airflow-memory-refresh"),
        "tenant_id": os.getenv("SOMAGENT_AIRFLOW_TENANT", "demo"),
        "capabilities": ["scheduler", "system"],
        "iat": now,
        "exp": now + int(os.getenv("SOMAGENT_AIRFLOW_JWT_TTL", "600")),
    }
    token = jwt.encode(payload, GATEWAY_SECRET, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


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
