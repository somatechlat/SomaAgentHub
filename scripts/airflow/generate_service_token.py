#!/usr/bin/env python3
"""Obtain a short-lived bearer token from the Identity Service.

This script requests a real token from the Identity Service `/v1/tokens/issue`
endpoint instead of generating an HS256 token locally. It prints the token to
stdout for use in `SOMAGENT_AIRFLOW_JWT`.
"""

from __future__ import annotations

import argparse
import os
import time
from typing import Any

import requests
from services.common.config.base_settings import resolve_env


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    now = int(time.time())
    return {
        "iss": args.issuer,
        "sub": args.subject,
        "tenant_id": args.tenant,
        "capabilities": args.capabilities,
        "iat": now,
        "exp": now + args.ttl,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "identity_url",
        nargs="?",
        default=resolve_env("IDENTITY_SERVICE_URL", "http://localhost:10002"),
        help="Identity Service base URL",
    )
    parser.add_argument(
        "--tenant", default=resolve_env("SOMAGENT_AIRFLOW_TENANT", "demo")
    )
    parser.add_argument(
        "--user",
        dest="user",
        default=resolve_env("SOMAGENT_AIRFLOW_SUBJECT", "airflow-service"),
        help="User ID for the token",
    )
    parser.add_argument(
        "--mfa",
        dest="mfa",
        default=resolve_env("SOMAGENT_AIRFLOW_MFA_CODE", ""),
        help="MFA code if required",
    )
    parser.add_argument(
        "--capabilities",
        nargs="*",
        default=["scheduler", "system"],
        help="Capabilities to embed in the token (space separated)",
    )
    parser.add_argument(
        "--ttl", type=int, default=600, help="Token lifetime in seconds"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url = f"{args.identity_url.rstrip('/')}/v1/tokens/issue"
    payload = {
        "tenant_id": args.tenant,
        "user_id": args.user,
        "mfa_code": args.mfa,
        "capabilities": args.capabilities,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
    except requests.RequestException as exc:
        raise SystemExit(f"Failed to reach Identity Service at {url}: {exc}")
    if resp.status_code != 200:
        raise SystemExit(f"Identity Service error {resp.status_code}: {resp.text}")
    data = resp.json()
    token = data.get("token")
    if not token:
        raise SystemExit("Identity Service response missing 'token'")
    print(token)


if __name__ == "__main__":
    main()
