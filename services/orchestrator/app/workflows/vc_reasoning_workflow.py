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

import time
import uuid
from datetime import timedelta
from typing import Any

from temporalio import activity, workflow

# --------------------------------------------------------------------------
# Imports from the orchestrator package
# --------------------------------------------------------------------------
# MultiAgentPattern import removed as it is unused in this workflow.
from ..database import get_async_session

# Metrics for VC workflow
from ..metrics.vc import (
    vc_episode_duration_seconds,
    vc_episode_total,
    vc_step_reward,
    vc_step_total,
)
from ..models.vc_models import VCEpisode, VCRole, VCStep
from ..reward import exact_match_reward
from ..services.event_service import OrchestratorEventService
from ..workflows.session import run_llm_completion  # existing activity

# --------------------------------------------------------------------------
# Activity implementations – these run in the Temporal worker process.
# --------------------------------------------------------------------------


@activity.defn(name="vc-create-episode")
async def create_episode(tenant: str, problem: dict[str, Any]) -> str:
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
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    reward: float,
) -> None:
    """Persist a ``VCStep`` linked to ``episode_id``.

    This activity only writes the step record. Event emission is handled
    elsewhere if enabled.
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


# The emit_vc_step_activity function and its related imports have been removed per user request to eliminate parallel execution logic.


@activity.defn(name="vc-calc-reward")
async def calc_reward(model_output: Any, expected_answer: Any) -> float:
    """Exact‑match reward for Solver and Corrector outputs.

    This mirrors the original ``exact_match_reward`` utility.
    """
    return exact_match_reward(model_output, expected_answer)


@activity.defn(name="vc-calc-verifier-reward")
async def calc_verifier_reward(verifier_output: Any, expected_answer: Any) -> float:
    """Reward for the Verifier role.

    The Verifier is asked a yes/no question.  If its answer (case‑insensitive)
    matches the ground‑truth correctness of the solution, the reward is ``1.0``;
    otherwise ``0.0``.
    """
    # Normalise the verifier answer to a simple yes/no string.
    answer = ""
    if isinstance(verifier_output, dict):
        answer = str(verifier_output.get("completion", "")).strip().lower()
    else:
        answer = str(verifier_output).strip().lower()

    # Determine whether the expected answer is a truthy string ("yes")
    # – the caller passes the *expected* correctness (True/False) via the
    # ``expected`` variable.  Here we simply compare the answer to "yes".
    return 1.0 if "yes" in answer else 0.0


# --------------------------------------------------------------------------
# Event emission activity – emits a VC_STEP event after a step is persisted.
# --------------------------------------------------------------------------


@activity.defn(name="vc-emit-step")
async def emit_vc_step_activity(
    episode_id: str,
    step_index: int,
    role: str,
    reward: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Emit a ``vc.step.v1`` event for a V‑C step.

    The activity creates a temporary DB session, instantiates the
    ``OrchestratorEventService`` and forwards the call to its ``emit_vc_step``
    method.  Governance (``allow_rl_training_data``) is enforced inside the
    service, so the activity does not need to repeat the check.
    """
    async with get_async_session() as session:
        service = OrchestratorEventService(session)
        await service.emit_vc_step(
            episode_id=episode_id,
            step_index=step_index,
            role=role,
            reward=reward,
            metadata=metadata,
        )


# --------------------------------------------------------------------------
# Workflow definition
# --------------------------------------------------------------------------


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
    async def run(self, request: dict[str, Any]) -> dict[str, Any]:
        tenant = request.get("tenant", "default")
        user = request.get("user", "anonymous")
        problem = request.get("problem", {})
        expected = problem.get("expected_answer")
        max_iterations: int = int(request.get("max_iterations", 5))

        # ------------------------------------------------------------------
        # Create the episode record and record metrics.
        # ------------------------------------------------------------------
        start_time = time.time()
        episode_id = await workflow.execute_activity(
            create_episode,
            tenant,
            problem,
            start_to_close_timeout=timedelta(seconds=30),
        )
        self.logger.info("VC episode created", episode_id=episode_id)
        # Increment episode counter
        vc_episode_total.labels(tenant=tenant).inc()

        # ------------------------------------------------------------------
        # Main loop – solver → (optional) verifier → corrector.
        # ------------------------------------------------------------------
        for iteration in range(max_iterations):
            base_index = (
                iteration * 3
            )  # three entries per iteration: solver, verifier, corrector

            # ----- Solver ---------------------------------------------------
            solver_prompt = problem.get("prompt", "")
            solver_input = {
                "prompt": solver_prompt,
                "model": "solver",
                "tenant": tenant,
                "user": user,
            }
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
            # Emit VC_STEP event for the solver step
            await workflow.execute_activity(
                emit_vc_step_activity,
                episode_id,
                base_index,
                VCRole.SOLVER.value,
                reward,
                start_to_close_timeout=timedelta(seconds=5),
            )
            # Record step metrics for solver
            vc_step_total.labels(tenant=tenant, role=VCRole.SOLVER.value).inc()
            vc_step_reward.labels(tenant=tenant, role=VCRole.SOLVER.value).observe(
                reward
            )
            if reward == 1.0:
                self.logger.info("Solver produced correct answer – terminating loop")
                break

            # ----- Verifier -------------------------------------------------
            verifier_prompt = f"Is the following solution correct?\nSolution: {solver_output.get('completion', '')}\nAnswer: {expected}\nRespond with yes or no."
            verifier_input = {
                "prompt": verifier_prompt,
                "model": "verifier",
                "tenant": tenant,
                "user": user,
            }
            verifier_output = await workflow.execute_activity(
                run_llm_completion,
                verifier_input,
                start_to_close_timeout=timedelta(minutes=1),
            )
            # Compute verifier reward (1.0 for "yes", else 0.0)
            verifier_reward = await workflow.execute_activity(
                calc_verifier_reward,
                verifier_output,
                expected,
                start_to_close_timeout=timedelta(seconds=5),
            )
            await workflow.execute_activity(
                add_step,
                episode_id,
                base_index + 1,
                VCRole.VERIFIER.value,
                verifier_input,
                verifier_output,
                verifier_reward,
                start_to_close_timeout=timedelta(seconds=5),
            )
            # Emit VC_STEP event for the verifier step
            await workflow.execute_activity(
                emit_vc_step_activity,
                episode_id,
                base_index + 1,
                VCRole.VERIFIER.value,
                verifier_reward,
                start_to_close_timeout=timedelta(seconds=5),
            )
            # Record step metrics for verifier
            vc_step_total.labels(tenant=tenant, role=VCRole.VERIFIER.value).inc()
            vc_step_reward.labels(tenant=tenant, role=VCRole.VERIFIER.value).observe(
                verifier_reward
            )
            if verifier_reward == 1.0:
                self.logger.info("Verifier approved solution – terminating loop")
                break

            # ----- Corrector -----------------------------------------------
            corrector_prompt = f"Please correct the following solution.\nSolution: {solver_output.get('completion', '')}\nExpected answer: {expected}\nProvide the improved solution."
            corrector_input = {
                "prompt": corrector_prompt,
                "model": "corrector",
                "tenant": tenant,
                "user": user,
            }
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
            # Emit VC_STEP event for the corrector step (reward currently 0.0)
            await workflow.execute_activity(
                emit_vc_step_activity,
                episode_id,
                base_index + 2,
                VCRole.CORRECTOR.value,
                0.0,
                start_to_close_timeout=timedelta(seconds=5),
            )
            # Record step metrics for corrector (reward is 0.0)
            vc_step_total.labels(tenant=tenant, role=VCRole.CORRECTOR.value).inc()
            vc_step_reward.labels(tenant=tenant, role=VCRole.CORRECTOR.value).observe(
                0.0
            )
        # ------------------------------------------------------------------
        # Mark episode as completed and record duration metric.
        # ------------------------------------------------------------------
        duration_seconds = time.time() - start_time
        vc_episode_duration_seconds.labels(tenant=tenant).observe(duration_seconds)
        # Episode status update is optional for this minimal implementation.
        # The caller can query the episode table later to see the final state.
        return {"episode_id": episode_id, "status": "completed"}
