#!/usr/bin/env python3
import sys
from pathlib import Path

# Add policy-engine directory to path so relative imports inside the package resolve
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from policy_app import evaluate_sync, EvalRequest

req = EvalRequest(session_id='s1', tenant='t1', user='u1', prompt='Hello world', role='dialogue_reasoning')
try:
    res = evaluate_sync(req)
    print(res.json())
except Exception as e:
    print(f"Evaluation failed: {e}")

req2 = EvalRequest(session_id='s2', tenant='t1', user='u2', prompt='This is forbidden content', role='dialogue_reasoning')
try:
    res2 = evaluate_sync(req2)
    print(res2.json())
except Exception as e:
    print(f"Evaluation failed: {e}")
