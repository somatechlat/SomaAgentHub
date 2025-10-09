#!/usr/bin/env python3
"""Utility to generate a short-lived JWT for Airflow service calls."""

from __future__ import annotations

import argparse
import os
import time
from typing import Any, Dict

import jwt


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
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
    parser.add_argument("secret", help="Shared gateway JWT secret (or set SOMAGENT_GATEWAY_JWT_SECRET)")
    parser.add_argument("--tenant", default=os.getenv("SOMAGENT_AIRFLOW_TENANT", "demo"))
    parser.add_argument("--subject", default=os.getenv("SOMAGENT_AIRFLOW_SUBJECT", "airflow-service"))
    parser.add_argument("--issuer", default="airflow")
    parser.add_argument(
        "--capabilities",
        nargs="*",
        default=["scheduler", "system"],
        help="Capabilities to embed in the token (space separated)",
    )
    parser.add_argument("--ttl", type=int, default=600, help="Token lifetime in seconds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    secret = args.secret or os.getenv("SOMAGENT_GATEWAY_JWT_SECRET")
    if not secret:
        raise SystemExit("Gateway secret must be provided")

    token = jwt.encode(build_payload(args), secret, algorithm="HS256")
    print(token)


if __name__ == "__main__":
    main()
