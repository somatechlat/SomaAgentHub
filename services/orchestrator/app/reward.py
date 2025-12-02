"""Simple reward utilities for the V‑C reasoning loop.

The MarsRL style loop requires a numeric reward for each step.  For the
initial implementation we use the most straightforward metric – an **exact
string match** between the model's output and a known correct answer.  The
function is deliberately pure (no side‑effects) so it can be unit‑tested in
isolation.

The expected answer is supplied by the caller (typically the ``problem``
payload) under the key ``expected_answer``.  If the answer is missing we
return ``0.0`` – this is safe and avoids crashes in production.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def exact_match_reward(model_output: Mapping[str, Any] | str, expected: Any) -> float:
    """Return ``1.0`` when the model output exactly matches ``expected``.

    Parameters
    ----------
    model_output:
        The raw output from the LLM activity.  It can be a dictionary (as
        returned by ``run_llm_completion``) that contains a ``completion``
        field, or a plain string.
    expected:
        The ground‑truth answer.  Anything that can be cast to ``str`` is
        accepted.

    Returns
    -------
    float
    ``1.0`` for an exact match (ignoring surrounding whitespace),
    otherwise ``0.0``.
    """

    if model_output is None:
        return 0.0

    # Extract the textual completion if a dict is provided.
    if isinstance(model_output, dict):
        # The activity ``run_llm_completion`` returns a dict with a key
        # ``completion`` that holds the generated text.
        text = model_output.get("completion") or ""
    else:
        text = str(model_output)

    expected_str = str(expected) if expected is not None else ""

    return 1.0 if text.strip() == expected_str.strip() else 0.0
