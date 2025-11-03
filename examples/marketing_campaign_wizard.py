#!/usr/bin/env python3
"""End-to-end marketing wizard example that hits live Gateway + Orchestrator."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests

DEFAULT_ANSWERS = {
    "campaign_name": "Fall 2025 AI Platform Launch",
    "campaign_type": "product_launch",
    "target_audience": [
        "Enterprise CTOs",
        "DevOps Engineers",
        "AI/ML Teams",
    ],
    "channels": ["email", "blog", "social_linkedin", "social_twitter"],
    "launch_date": "2025-10-21",
    "budget": 10000,
    "key_messages": (
        "Revolutionary AI agent platform. 10x faster deployment. "
        "Enterprise-grade security. Open-source foundation."
    ),
    "success_metrics": ["impressions", "clicks", "leads", "signups", "engagement"],
    "brand_voice": "professional",
    "approval_required": True,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the marketing campaign wizard against a live SomaAgentHub stack."
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("SOMAGENT_GATEWAY_URL", "http://localhost:10000"),
        help="Gateway API base URL (default: %(default)s or env SOMAGENT_GATEWAY_URL).",
    )
    parser.add_argument(
        "--user-id",
        default=os.getenv("SOMAGENT_DEMO_USER", "demo-agent"),
        help="User ID to associate with the wizard session (default: %(default)s).",
    )
    parser.add_argument(
        "--answers-file",
        type=Path,
        help="Optional JSON file containing overrides for wizard answers.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for each answer instead of using defaults.",
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Automatically approve the generated execution plan.",
    )
    parser.add_argument(
        "--orchestrator-url",
        default=os.getenv("SOMAGENT_GATEWAY_ORCHESTRATOR_URL")
        or os.getenv("ORCHESTRATOR_URL")
        or "http://localhost:10001",
        help="Orchestrator base URL for status polling (default: %(default)s).",
    )
    parser.add_argument(
        "--poll-orchestrator",
        action="store_true",
        help="Poll the orchestrator for workflow status after approval.",
    )
    parser.add_argument(
        "--plan-output",
        type=Path,
        help="Write the generated execution plan JSON to this path.",
    )
    parser.add_argument(
        "--max-poll-seconds",
        type=int,
        default=120,
        help="Maximum seconds to poll orchestrator status (default: %(default)s).",
    )
    return parser


def load_answers(path: Path | None) -> Dict[str, Any]:
    answers = dict(DEFAULT_ANSWERS)
    if not path:
        return answers
    data = json.loads(path.read_text())
    answers.update(data)
    return answers


def fetch_wizards(base_url: str) -> List[Dict[str, Any]]:
    resp = requests.get(f"{base_url}/v1/wizards", timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("wizards", [])


def find_wizard(wizards: Iterable[Dict[str, Any]], wizard_id: str) -> Dict[str, Any] | None:
    for wizard in wizards:
        if wizard.get("wizard_id") == wizard_id:
            return wizard
    return None


def start_session(base_url: str, wizard_id: str, user_id: str) -> Dict[str, Any]:
    resp = requests.post(
        f"{base_url}/v1/wizards/start",
        json={"wizard_id": wizard_id, "user_id": user_id},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def prompt_for_answer(question: Dict[str, Any], default: Any) -> Any:
    prompt = f"{question['prompt']} "
    if default not in (None, ""):
        prompt += f"[default: {default}] "
    answer = input(prompt).strip()
    if not answer and default is not None:
        return default

    qtype = question.get("type")
    if qtype == "multi_select":
        return [item.strip() for item in answer.split(",") if item.strip()]
    if qtype == "number":
        return float(answer) if "." in answer else int(answer)
    if qtype == "boolean":
        lowered = answer.lower()
        return lowered in {"true", "t", "yes", "y", "1"}
    return answer


def encode_answer(question: Dict[str, Any], value: Any) -> Any:
    qtype = question.get("type")
    if qtype == "multi_select":
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
    if qtype == "multi_text":
        if isinstance(value, (list, tuple)):
            return ", ".join(str(item) for item in value)
    if qtype == "number":
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            return float(value) if "." in value else int(value)
    if qtype == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in {"true", "t", "yes", "y", "1"}:
                return True
            if lowered in {"false", "f", "no", "n", "0"}:
                return False
    return value


def answer_question(base_url: str, session_id: str, question: Dict[str, Any], value: Any) -> Dict[str, Any]:
    encoded = encode_answer(question, value)
    resp = requests.post(
        f"{base_url}/v1/wizards/{session_id}/answer",
        json={"value": encoded},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def approve_plan(base_url: str, session_id: str) -> Dict[str, Any]:
    resp = requests.post(f"{base_url}/v1/wizards/{session_id}/approve", timeout=15)
    resp.raise_for_status()
    return resp.json()


def poll_orchestrator(orchestrator_url: str, workflow_id: str, timeout_seconds: int) -> Dict[str, Any]:
    end_time = time.time() + timeout_seconds
    status_payload: Dict[str, Any] = {}
    while time.time() < end_time:
        resp = requests.get(f"{orchestrator_url}/v1/mao/{workflow_id}", timeout=10)
        if resp.status_code == 404:
            time.sleep(2)
            continue
        resp.raise_for_status()
        status_payload = resp.json()
        status = status_payload.get("status")
        if status in {"completed", "failed", "cancelled"}:
            break
        time.sleep(5)
    return status_payload


def save_plan(plan: Dict[str, Any], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    print(f"🔌 Gateway: {args.api_url}")
    print(f"👤 User   : {args.user_id}")

    wizards = fetch_wizards(args.api_url)
    wizard = find_wizard(wizards, "marketing_campaign_v1")
    if not wizard:
        print("❌ marketing_campaign_v1 wizard not available. Current wizards:")
        print(json.dumps(wizards, indent=2))
        return 1

    print(f"🧙 Wizard : {wizard['title']} (version {wizard.get('version')})")

    session = start_session(args.api_url, "marketing_campaign_v1", args.user_id)
    session_id = session["session_id"]
    print(f"🆔 Session: {session_id}")

    answers = load_answers(args.answers_file)
    current_question = session.get("question")

    while current_question:
        qid = current_question.get("id")
        default_value = answers.get(qid)

        if args.interactive:
            if default_value is None:
                default_value = ""
            user_value = prompt_for_answer(current_question, default_value)
        else:
            if default_value is None:
                raise ValueError(f"No answer provided for required question '{qid}'")
            user_value = default_value

        print(f"   → {qid}: {encode_answer(current_question, user_value)}")
        response = answer_question(args.api_url, session_id, current_question, user_value)
        if response.get("completed"):
            summary = response["summary"]
            execution_plan = response["execution_plan"]
            print("✅ Wizard completed.")
            print("📋 Summary:")
            print(json.dumps(summary, indent=2))
            print("🛠️  Execution plan:")
            print(json.dumps(execution_plan, indent=2))

            if args.plan_output:
                save_plan(execution_plan, args.plan_output)
                print(f"💾 Plan saved to {args.plan_output}")

            if args.approve:
                print("🚀 Approving execution plan...")
                approval_response = approve_plan(args.api_url, session_id)
                print(json.dumps(approval_response, indent=2))

                workflow_id = approval_response.get("workflow_id")
                if args.poll_orchestrator and workflow_id:
                    print(f"⏱️ Polling orchestrator {args.orchestrator_url} for workflow {workflow_id}...")
                    status_payload = poll_orchestrator(
                        args.orchestrator_url, workflow_id, args.max_poll_seconds
                    )
                    print("📈 Orchestrator status:")
                    print(json.dumps(status_payload, indent=2))

            break

        current_question = response.get("question")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc.response.status_code} {exc.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
