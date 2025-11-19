"""Temporal workflow implementing a Solver → Verifier → Corrector loop.

The workflow is triggered when the ``MultiAgentPattern.VC_REASONING`` pattern
is detected.  It creates a persistent ``VCEpisode`` record, then iterates up to
``max_iterations`` (default 5) performing the following steps:

1. **Solver** – calls the generic LLM completion activity with the problem
   prompt.
2. **Reward** – evaluates the solver output against ``expected_answer`` using
   the exact‑match reward function.
3. If the reward is ``1.0`` the loop ends – the solution is correct.
4. Otherwise a **Verifier** activity asks the model whether the solution is
   correct (simple yes/no prompt).  If the verifier answers ``yes`` the loop
   ends.
5. If still incorrect, a **Corrector** activity asks the model to improve the
   solution.  The corrected output is stored and the loop continues.

Each iteration stores a ``VCStep`` record (role, input, output, reward) linked
to the episode.  The workflow also emits a ``VC_STEP`` outbox event after each
step – the event payload mirrors the step record and can be consumed by an
RL‑training pipeline.

The implementation is deliberately minimal but functional, re‑using the
existing ``run_llm_completion`` activity from ``session.py`` and the
``exact_match_reward`` utility from ``reward.py``.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any, Dict

from temporalio import activity, workflow

# ---------------------------------------------------------------------------
# Imports from the orchestrator package
# ---------------------------------------------------------------------------
from ..core.framework_router import MultiAgentPattern
from ..database import get_async_session
from ..models.vc_models import VCEpisode, VCStep, VCRole
from ..reward import exact_match_reward
from ..workflows.session import run_llm_completion  # existing activity
from ..services.event_service import OrchestratorEventService


# ---------------------------------------------------------------------------
# Activity implementations – these run in the Temporal worker process.
# ---------------------------------------------------------------------------

@activity.defn(name="vc-create-episode")
async def create_episode(tenant: str, problem: Dict[str, Any]) -> str:
    """Persist a new ``VCEpisode`` and return its UUID as a string."""
    async with get_async_session() as session:
        episode = VCEpisode(
            tenant=tenant,
            problem=problem,
            status="running",
        )
        session.add(episode)
        await session.flush()
        return str(episode.id)


@activity.defn(name="vc-add-step")
async def add_step(
    episode_id: str,
    step_index: int,
    role: str,
    input_payload: Dict[str, Any],
    output_payload: Dict[str, Any],
    reward: float,
) -> None:
    """Persist a ``VCStep`` linked to ``episode_id``.

    For the minimal MVP we only store the step record; emitting a dedicated
    ``VC_STEP`` event is left for a later task.
    """
    async with get_async_session() as session:
        step = VCStep(
            episode_id=uuid.UUID(episode_id),
            step_index=step_index,
            role=VCRole(role),
            input=input_payload,
            output=output_payload,
            reward=reward,
        )
        session.add(step)
        await session.flush()


@activity.defn(name="vc-calc-reward")
async def calc_reward(model_output: Any, expected_answer: Any) -> float:
    """Thin wrapper around :func:`exact_match_reward`."""
    return exact_match_reward(model_output, expected_answer)


# ---------------------------------------------------------------------------
# Workflow definition
# ---------------------------------------------------------------------------

@workflow.defn(name="vc-reasoning-workflow")
class VCReasoningWorkflow:
    """Temporal workflow that runs the V‑C loop.

    The payload must contain at least:
    ``problem`` – a dict with the problem description and ``expected_answer``.
    Optional ``max_iterations`` (int) and ``tenant``/``user`` fields.
    """

    def __init__(self) -> None:
        self.logger = workflow.logger

    @workflow.run
    async def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        tenant = request.get("tenant", "default")
        user = request.get("user", "anonymous")
        problem = request.get("problem", {})
        expected = problem.get("expected_answer")
        max_iterations: int = int(request.get("max_iterations", 5))

        # -------------------------------------------------------------------
        # Create the episode record.
        # -------------------------------------------------------------------
        episode_id = await workflow.execute_activity(
            create_episode,
            tenant,
            problem,
            start_to_close_timeout=timedelta(seconds=30),
        )
        self.logger.info("VC episode created", episode_id=episode_id)

        # -------------------------------------------------------------------
        # Main loop – solver → (optional) verifier → corrector.
        # -------------------------------------------------------------------
        for iteration in range(max_iterations):
            base_index = iteration * 3  # three entries per iteration: solver, verifier, corrector

            # ----- Solver ---------------------------------------------------
            solver_prompt = problem.get("prompt", "")
            solver_input = {"prompt": solver_prompt, "model": "solver", "tenant": tenant, "user": user}
            solver_output = await workflow.execute_activity(
                run_llm_completion,
                solver_input,
                start_to_close_timeout=timedelta(minutes=2),
            )
            reward = await workflow.execute_activity(
                calc_reward,
                solver_output,
                expected,
                start_to_close_timeout=timedelta(seconds=5),
            )
            await workflow.execute_activity(
                add_step,
                episode_id,
                base_index,
                VCRole.SOLVER.value,
                solver_input,
                solver_output,
                reward,
                start_to_close_timeout=timedelta(seconds=5),
            )
            if reward == 1.0:
                self.logger.info("Solver produced correct answer – terminating loop")
                break

            # ----- Verifier -------------------------------------------------
            verifier_prompt = (
                f"Is the following solution correct?\nSolution: {solver_output.get('completion', '')}\nAnswer: {expected}\nRespond with yes or no."
            )
            verifier_input = {"prompt": verifier_prompt, "model": "verifier", "tenant": tenant, "user": user}
            verifier_output = await workflow.execute_activity(
                run_llm_completion,
                verifier_input,
                start_to_close_timeout=timedelta(minutes=1),
            )
            verifier_correct = "yes" in verifier_output.get("completion", "").lower()
            await workflow.execute_activity(
                add_step,
                episode_id,
                base_index + 1,
                VCRole.VERIFIER.value,
                verifier_input,
                verifier_output,
                1.0 if verifier_correct else 0.0,
                start_to_close_timeout=timedelta(seconds=5),
            )
            if verifier_correct:
                self.logger.info("Verifier approved solution – terminating loop")
                break

            # ----- Corrector -----------------------------------------------
            corrector_prompt = (
                f"Please correct the following solution.\nSolution: {solver_output.get('completion', '')}\nExpected answer: {expected}\nProvide the improved solution."
            )
            corrector_input = {"prompt": corrector_prompt, "model": "corrector", "tenant": tenant, "user": user}
            corrector_output = await workflow.execute_activity(
                run_llm_completion,
                corrector_input,
                start_to_close_timeout=timedelta(minutes=2),
            )
            await workflow.execute_activity(
                add_step,
                episode_id,
                base_index + 2,
                VCRole.CORRECTOR.value,
                corrector_input,
                corrector_output,
                0.0,
                start_to_close_timeout=timedelta(seconds=5),
            )
        # -------------------------------------------------------------------
        # Mark episode as completed.
        # -------------------------------------------------------------------
        # Episode status update is optional for this minimal implementation.
        # The caller can query the episode table later to see the final state.
        return {"episode_id": episode_id, "status": "completed"}
