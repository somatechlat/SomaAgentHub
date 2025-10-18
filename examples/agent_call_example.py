# Example: Agent invoking SomaAgentHub API
"""
`agent_call_example.py` demonstrates a **real** end-to-end interaction with
SomaAgentHub using the Python SDK. The flow keeps dependencies minimal so you
can copy/paste it into your own automation scripts.

Scenario:
1. Perform a health check to verify connectivity.
2. Start a new conversation (or reuse one via CLI flag).
3. Send a user message and display the assistant reply plus metadata.

Run it with:

```bash
python examples/agent_call_example.py \
  --message "Draft a welcome email for new users." \
  --api-url http://localhost:10000 \
  --api-key "$SOMAAGENT_API_KEY"
```

The script exits non-zero if the request fails, ensuring it can be embedded in CI
pipelines. See `--help` for all options.
"""

# EXAMPLE_AGENT_CALL

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

try:
    from somaagent import AsyncSomaAgentClient
except ImportError as exc:  # pragma: no cover - helpful guidance
    raise ImportError(
        "Unable to import 'somaagent'. Install the SDK with "
        "'pip install -r requirements-dev.txt' or 'pip install -e sdk/python'."
    ) from exc


def _env_default(name: str, fallback: Optional[str] = None) -> Optional[str]:
    """Return environment override if present."""

    value = os.getenv(name)
    if value:
        return value
    return fallback


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call SomaAgentHub via Python SDK")
    parser.add_argument(
        "--message",
        required=False,
        default="Hello SomaAgentHub! Can you summarise the project roadmap?",
        help="Message to send to the agent (default: friendly greeting).",
    )
    parser.add_argument(
        "--api-url",
        default=_env_default("SOMAAGENT_API_URL", "http://localhost:10000"),
        help="Base URL for SomaAgentHub (env: SOMAAGENT_API_URL).",
    )
    parser.add_argument(
        "--api-key",
        default=_env_default("SOMAAGENT_API_KEY"),
        help="API key/token if authentication is enabled (env: SOMAAGENT_API_KEY).",
    )
    parser.add_argument(
        "--conversation-id",
        default=_env_default("SOMAAGENT_CONVERSATION_ID"),
        help="Reuse an existing conversation id instead of creating a fresh one.",
    )
    parser.add_argument(
        "--dump-json",
        action="store_true",
        help="Print the full JSON payload returned by the API for debugging.",
    )
    return parser


async def run_example(args: argparse.Namespace) -> Dict[str, Any]:
    """Execute the example workflow and return structured result."""

    async with AsyncSomaAgentClient(
        base_url=args.api_url, api_key=args.api_key
    ) as client:
        # 1. Health check (API exposes /health for readiness)
        health = await client.health()

        # 2. Figure out conversation context
        conversation_id = args.conversation_id
        if not conversation_id:
            conversation = await client.create_conversation(
                metadata={"source": "examples/agent_call", "purpose": "demo"}
            )
            conversation_id = conversation.id

        # 3. Send message
        reply = await client.send_message(
            conversation_id=conversation_id,
            content=args.message,
        )

        response_text = reply.content
        result = {
            "health": health,
            "conversation_id": conversation_id,
            "message": args.message,
            "response": response_text,
        }
        return result


def pretty_print(result: Dict[str, Any], *, dump_json: bool = False) -> None:
    """Display example results in a friendly format."""

    if dump_json:
        print(json.dumps(result, indent=2))
        return

    print("✅ SomaAgentHub reachable")
    print(f"   → version: {result['health'].get('version', 'unknown')}")
    print(f"   → status : {result['health'].get('status', 'n/a')}")
    print()
    print(f"🧵 Conversation: {result['conversation_id']}")
    print(f"🙋 User: {result['message']}")
    print(f"🤖 Assistant:\n{result['response']}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = asyncio.run(run_example(args))
    except Exception as exc:  # pragma: no cover - CLI guardrail
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    pretty_print(result, dump_json=args.dump_json)


if __name__ == "__main__":
    main()
