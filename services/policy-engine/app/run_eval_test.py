#!/usr/bin/env python3
"""Manual evaluation harness for local debugging.

Pytest will skip this module during automated test runs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="utility script for manual execution only")

# Add policy-engine directory to path so relative imports inside the package resolve
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.policy_app import EvalRequest, evaluate_sync  # noqa: E402


def main() -> None:
    req = EvalRequest(session_id="s1", tenant="t1", user="u1", prompt="Hello world", role="dialogue_reasoning")
    try:
        res = evaluate_sync(req)
        print(res.model_dump_json(indent=2))
    except Exception as exc:  # pragma: no cover - manual harness
        print(f"Evaluation failed: {exc}")

    req2 = EvalRequest(
        session_id="s2",
        tenant="t1",
        user="u2",
        prompt="This is forbidden content",
        role="dialogue_reasoning",
    )
    try:  # pragma: no cover - manual harness
        res2 = evaluate_sync(req2)
        print(res2.model_dump_json(indent=2))
    except Exception as exc:
        print(f"Evaluation failed: {exc}")


if __name__ == "__main__":  # pragma: no cover - manual harness
    main()
