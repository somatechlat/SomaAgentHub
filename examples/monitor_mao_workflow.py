#!/usr/bin/env python3
"""Monitor a Multi-Agent Orchestrator workflow until completion."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import requests

TERMINAL_STATUSES = {"completed", "failed", "cancelled", "terminated"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Poll a running MAO workflow and print status/result details."
    )
    parser.add_argument(
        "workflow_id",
        help="Workflow ID returned by the wizard approval step (e.g. mao-mao-xxxx).",
    )
    parser.add_argument(
        "--orchestrator-url",
        default=os.getenv("SOMAGENT_GATEWAY_ORCHESTRATOR_URL")
        or os.getenv("ORCHESTRATOR_URL")
        or "http://localhost:10001",
        help="Base URL for the orchestrator service (default: %(default)s).",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between status checks (default: %(default)s).",
    )
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=300,
        help="Total seconds to wait before giving up (default: %(default)s).",
    )
    parser.add_argument(
        "--show-history-length",
        action="store_true",
        help="Log workflow history length on each poll tick.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw JSON responses instead of formatted text.",
    )
    return parser


def fetch_status(orchestrator_url: str, workflow_id: str) -> dict[str, Any]:
    resp = requests.get(f"{orchestrator_url}/v1/mao/{workflow_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def print_status(payload: dict[str, Any], *, raw: bool, show_history: bool) -> None:
    if raw:
        print(json.dumps(payload, indent=2))
        return

    status = payload.get("status", "unknown")
    history_length = payload.get("history_length")
    run_id = payload.get("run_id")
    print(f"status: {status}")
    if run_id:
        print(f"run_id: {run_id}")
    if show_history and history_length is not None:
        print(f"history_length: {history_length}")

    result = payload.get("result")
    if result:
        print("result:")
        print(json.dumps(result, indent=2))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    end_time = time.time() + args.max_seconds

    print(f"🛰️  Orchestrator: {args.orchestrator_url}")
    print(f"🧠 Workflow    : {args.workflow_id}")
    print("---")

    last_status = None
    while time.time() < end_time:
        try:
            payload = fetch_status(args.orchestrator_url, args.workflow_id)
        except requests.HTTPError as exc:
            print(
                f"HTTP error: {exc.response.status_code} {exc.response.text}",
                file=sys.stderr,
            )
            return 1
        except Exception as exc:  # pragma: no cover - network edge cases
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        status = payload.get("status", "unknown")
        if status != last_status:
            print_status(payload, raw=args.raw, show_history=args.show_history_length)
            print("---")
            last_status = status
        elif args.show_history_length:
            print_status(payload, raw=args.raw, show_history=True)
            print("---")

        if status.lower() in TERMINAL_STATUSES:
            print("✅ Workflow reached terminal state.")
            return 0

        time.sleep(args.poll_interval)

    print("⚠️  Timeout reached before workflow completed.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
