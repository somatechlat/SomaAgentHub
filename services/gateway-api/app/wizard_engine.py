"""Wizard Engine - Interactive project setup and campaign creation."""

from __future__ import annotations

import logging
from services.common.config.base_settings import resolve_env
import re
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
import yaml
from pydantic import BaseModel, Field
from services.common.contracts.pricing import BudgetPrecheckDecision
from sqlalchemy.ext.asyncio import AsyncSession

# Local import guard: gateway_api package may not exist when loaded as plain module in tests
try:
    from gateway_api.app.services.event_service import GatewayEventService  # type: ignore
except Exception:  # pragma: no cover
    GatewayEventService = None  # type: ignore
from services.common.events.publisher import EventPublisher
from services.orchestrator.app.repository.outbox_event_repository import OutboxEventRepository

logger = logging.getLogger(__name__)


class WizardQuestion(BaseModel):
    """Individual wizard question definition."""

    id: str
    step: int
    prompt: str
    type: str  # text, select, multi_select, date, boolean, number, etc.
    required: bool = True
    options: list[dict[str, Any]] | None = None
    default: Any | None = None
    placeholder: str | None = None
    help: str | None = None
    validation: dict[str, Any] | None = None


class WizardSession(BaseModel):
    """Active wizard session state."""

    session_id: str
    wizard_id: str
    user_id: str
    current_step: int = 1
    answers: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class WizardModule(BaseModel):
    """Execution module after wizard completion."""

    id: str
    title: str
    agent: str
    dependencies: list[str]
    tasks: list[dict[str, Any]]
    outputs: list[str]
    condition: str | None = None
    status: str = "pending"  # pending, in_progress, completed, failed


class WizardEngine:
    """Core wizard engine for interactive project setup."""

    def __init__(self):
        self.wizards_path = Path(__file__).parent / "wizards"
        self.sessions: dict[str, WizardSession] = {}
        self.wizard_schemas: dict[str, dict] = {}
        self._load_wizard_schemas()

    def _load_wizard_schemas(self):
        """Load all wizard YAML schemas from the wizards directory."""
        if not self.wizards_path.exists():
            return

        for yaml_file in self.wizards_path.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    schema = yaml.safe_load(f)
                    wizard_id = schema.get("wizard_id")
                    if wizard_id:
                        self.wizard_schemas[wizard_id] = schema
            except Exception as e:
                logger.warning("Error loading wizard schema %s: %s", yaml_file, e)

    def list_wizards(self) -> list[dict[str, Any]]:
        """List all available wizards."""
        return [
            {
                "wizard_id": wiz_id,
                "title": schema.get("title"),
                "description": schema.get("description"),
                "version": schema.get("version"),
                "estimated_duration": schema.get("estimated_duration", {}).get("total"),
            }
            for wiz_id, schema in self.wizard_schemas.items()
        ]

    def start_wizard(self, wizard_id: str, user_id: str, metadata: dict | None = None) -> dict[str, Any]:
        """Start a new wizard session."""
        if wizard_id not in self.wizard_schemas:
            raise ValueError(f"Wizard '{wizard_id}' not found")

        session_id = f"wiz-{uuid.uuid4().hex[:12]}"
        session = WizardSession(
            session_id=session_id,
            wizard_id=wizard_id,
            user_id=user_id,
            metadata=metadata or {},
        )

        self.sessions[session_id] = session

        # Get first question
        first_question = self._get_current_question(session)

        return {
            "session_id": session_id,
            "wizard_id": wizard_id,
            "wizard_title": self.wizard_schemas[wizard_id].get("title"),
            "current_step": 1,
            "total_steps": len(self.wizard_schemas[wizard_id].get("questions", [])),
            "question": first_question,
            "progress": self._calculate_progress(session),
        }

    def _get_current_question(self, session: WizardSession) -> dict[str, Any] | None:
        """Get the current question for the session."""
        schema = self.wizard_schemas.get(session.wizard_id)
        if not schema:
            return None

        questions = schema.get("questions", [])

        # Find question for current step
        for q in questions:
            if q.get("step") == session.current_step:
                return {
                    "id": q.get("id"),
                    "step": q.get("step"),
                    "prompt": q.get("prompt"),
                    "type": q.get("type"),
                    "required": q.get("required", True),
                    "options": q.get("options"),
                    "default": q.get("default"),
                    "placeholder": q.get("placeholder"),
                    "help": q.get("help"),
                }

        return None

    def submit_answer(self, session_id: str, answer: dict[str, Any]) -> dict[str, Any]:
        """Submit an answer and advance to next question."""
        if session_id not in self.sessions:
            raise ValueError(f"Session '{session_id}' not found")

        session = self.sessions[session_id]
        schema = self.wizard_schemas[session.wizard_id]

        # Get current question
        current_question = self._get_current_question(session)
        if not current_question:
            raise ValueError("No current question found")

        # Validate answer
        question_id = current_question["id"]
        answer_value = answer.get("value")

        if current_question.get("required") and not answer_value:
            raise ValueError(f"Answer required for question '{question_id}'")

        # Store answer
        session.answers[question_id] = answer_value

        # Move to next step
        session.current_step += 1

        # Check if wizard is complete
        total_steps = len(schema.get("questions", []))
        if session.current_step > total_steps:
            session.completed = True
            return self._complete_wizard(session)

        # Get next question
        next_question = self._get_current_question(session)

        return {
            "session_id": session_id,
            "current_step": session.current_step,
            "total_steps": total_steps,
            "question": next_question,
            "progress": self._calculate_progress(session),
            "completed": False,
        }

    def _calculate_progress(self, session: WizardSession) -> dict[str, Any]:
        """Calculate wizard completion progress."""
        schema = self.wizard_schemas[session.wizard_id]
        total_steps = len(schema.get("questions", []))
        completed_steps = session.current_step - 1

        return {
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "percentage": (int((completed_steps / total_steps) * 100) if total_steps > 0 else 0),
        }

    def _complete_wizard(self, session: WizardSession) -> dict[str, Any]:
        """Complete wizard and prepare execution plan."""
        schema = self.wizard_schemas[session.wizard_id]

        # Build execution plan
        raw_modules = [
            WizardModule(
                id=module_def["id"],
                title=module_def["title"],
                agent=module_def["agent"],
                dependencies=module_def.get("dependencies", []),
                tasks=module_def.get("tasks", []),
                outputs=module_def.get("outputs", []),
                condition=module_def.get("condition"),
                status=module_def.get("status", "pending"),
            ).model_dump()
            for module_def in schema.get("modules", [])
        ]

        # Interpolate answers into tasks and cache the plan for approval step
        execution_plan = self._build_execution_plan(session, raw_modules)
        session.metadata["_execution_plan"] = execution_plan

        return {
            "session_id": session.session_id,
            "completed": True,
            "progress": {
                "completed_steps": session.current_step,
                "total_steps": session.current_step,
                "percentage": 100,
            },
            "summary": {
                "wizard_id": session.wizard_id,
                "wizard_title": schema.get("title"),
                "answers": session.answers,
                "started_at": session.started_at.isoformat(),
                "completed_at": datetime.now(UTC).isoformat(),
            },
            "execution_plan": execution_plan,
            "next_steps": {
                "action": "approve_and_execute",
                "message": "Review the execution plan and approve to start the campaign automation",
                "endpoints": {
                    "approve": f"/v1/wizard/{session.session_id}/approve",
                    "modify": f"/v1/wizard/{session.session_id}/modify",
                },
            },
        }

    def _build_execution_plan(self, session: WizardSession, modules: list[dict]) -> dict[str, Any]:
        """Build detailed execution plan from wizard answers."""
        schema = self.wizard_schemas[session.wizard_id]

        # Interpolate variables
        def interpolate(text: str) -> str:
            """Replace {variable} with actual answers."""
            if not isinstance(text, str):
                return text
            result = text
            for key, value in session.answers.items():
                replacement = self._render_answer(value)
                result = result.replace(f"{{{key}}}", replacement)
            return result

        raw_modules = modules or []

        enabled_modules = [
            module
            for module in raw_modules
            if not module.get("condition") or self._evaluate_condition(module["condition"], session.answers)
        ]
        enabled_ids = {module["id"] for module in enabled_modules}

        processed_modules = []
        for module in enabled_modules:
            processed = module.copy()
            processed["id"] = module["id"]
            processed["agent"] = module["agent"]
            processed["title"] = interpolate(module["title"])
            processed["dependencies"] = [dep for dep in module.get("dependencies", []) if dep in enabled_ids]

            # Interpolate task descriptions, params, and conditional logic
            processed_tasks = []
            for task in module.get("tasks", []):
                logic_branches = task.get("logic")
                if logic_branches:
                    for branch in logic_branches:
                        if not self._evaluate_condition(branch.get("if", ""), session.answers):
                            continue
                        branch_action = branch.get("then")
                        branch_params = branch.get("params", {})
                        processed_tasks.append(
                            {
                                "action": branch_action,
                                "description": interpolate(branch.get("description") or f"Execute {branch_action}"),
                                "params": self._interpolate_value(branch_params, session.answers, interpolate),
                            }
                        )
                    continue

                processed_task = {
                    "action": task["action"],
                    "description": interpolate(task.get("description", "")),
                    "params": {},
                }

                # Interpolate params
                params = task.get("params", {})
                if params:
                    processed_task["params"] = self._interpolate_value(params, session.answers, interpolate)

                processed_tasks.append(processed_task)

            processed["tasks"] = processed_tasks
            processed_modules.append(processed)

        return {
            "plan_id": f"plan-{session.session_id}",
            "campaign_name": session.answers.get("campaign_name", "Untitled Campaign"),
            "launch_date": session.answers.get("launch_date"),
            "modules": processed_modules,
            "estimated_duration": schema.get("estimated_duration", {}).get("total"),
            "agents_required": sorted({m["agent"] for m in processed_modules}),
            "tools_required": self._extract_required_tools(processed_modules),
            "success_criteria": schema.get("success_criteria", {}),
        }

    @staticmethod
    def _render_answer(value: Any) -> str:
        """Render an answer value for interpolation within strings."""
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def _interpolate_value(self, value: Any, answers: dict[str, Any], interpolate) -> Any:
        """Recursively interpolate values containing answer placeholders."""
        if isinstance(value, dict):
            return {key: self._interpolate_value(val, answers, interpolate) for key, val in value.items()}
        if isinstance(value, list):
            return [self._interpolate_value(item, answers, interpolate) for item in value]
        if isinstance(value, str):
            placeholder_match = re.fullmatch(r"\{([^{}]+)\}", value.strip())
            if placeholder_match:
                key = placeholder_match.group(1)
                return answers.get(key, "")
            return interpolate(value)
        return value

    def _evaluate_condition(self, expression: str, answers: dict[str, Any]) -> bool:
        """Evaluate simple condition expressions against collected answers."""
        expr = (expression or "").strip()
        if not expr:
            return True

        # Normalize boolean keywords
        expr = expr.replace(" true", " True").replace(" false", " False")

        if " contains " in expr:
            field, value = expr.split(" contains ", 1)
            field = field.strip()
            target = self._strip_quotes(value.strip())
            field_value = answers.get(field)
            if isinstance(field_value, str):
                candidates = [item.strip() for item in field_value.split(",")]
            elif isinstance(field_value, list):
                candidates = [str(item) for item in field_value]
            else:
                return False
            return target in candidates

        for operator in ("==", "!=", ">=", "<=", ">", "<"):
            if operator in expr:
                left, right = expr.split(operator, 1)
                left_value = answers.get(left.strip())
                right_value = self._coerce_literal(self._strip_quotes(right.strip()))
                return self._compare(left_value, right_value, operator)

        return False

    @staticmethod
    def _strip_quotes(value: str) -> str:
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        return value

    @staticmethod
    def _coerce_literal(value: str) -> Any:
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    @staticmethod
    def _compare(left: Any, right: Any, operator: str) -> bool:
        try:
            if operator == "==":
                return left == right
            if operator == "!=":
                return left != right
            if operator == ">":
                return left > right
            if operator == "<":
                return left < right
            if operator == ">=":
                return left >= right
            if operator == "<=":
                return left <= right
        except TypeError:
            return False
        return False

    def _extract_required_tools(self, modules: list[dict]) -> list[str]:
        """Extract unique list of tools required for execution."""
        tools = set()
        for module in modules:
            for task in module.get("tasks", []):
                action = task.get("action", "")
                if "." in action:
                    tool = action.split(".")[0]
                    tools.add(tool)
        return sorted(list(tools))

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get wizard session details."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        schema = self.wizard_schemas.get(session.wizard_id)

        return {
            "session_id": session.session_id,
            "wizard_id": session.wizard_id,
            "wizard_title": schema.get("title") if schema else None,
            "current_step": session.current_step,
            "total_steps": len(schema.get("questions", [])) if schema else 0,
            "answers": session.answers,
            "completed": session.completed,
            "started_at": session.started_at.isoformat(),
            "progress": self._calculate_progress(session),
        }

    def approve_execution(self, session_id: str) -> dict[str, Any]:
        """Approve wizard execution plan and trigger real orchestration via Orchestrator."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found")

        if not session.completed:
            raise ValueError("Wizard must be completed before approval")

        # Build a minimal multi-agent orchestration request from the execution plan
        schema = self.wizard_schemas.get(session.wizard_id)
        modules = schema.get("modules", []) if schema else []
        plan = session.metadata.get("_execution_plan") or self._build_execution_plan(session, modules)
        session.metadata["_execution_plan"] = plan
        directives: list[dict[str, Any]] = []
        for module in plan.get("modules", []):
            module_tasks = module.get("tasks", [])
            capability_names = {
                (task.get("action", "").split(".")[0] if "." in task.get("action", "") else task.get("action", ""))
                for task in module_tasks
                if task.get("action")
            }
            prompt_lines = [f"{module.get('title', 'Execute module')} for campaign {plan.get('campaign_name', '')}"]
            if module_tasks:
                prompt_lines.append("Key tasks:")
                prompt_lines.extend(
                    f"- {task.get('description', task.get('action'))}"
                    for task in module_tasks
                    if task.get("description") or task.get("action")
                )

            directives.append(
                {
                    "agent_id": module.get("agent", module.get("id", "agent")),
                    "goal": module.get("title", "Execute module"),
                    "prompt": "\n".join(prompt_lines),
                    "capabilities": sorted(capability_names),
                    "metadata": {
                        "module_id": module.get("id"),
                        "dependencies": module.get("dependencies", []),
                        "tasks": module_tasks,
                    },
                }
            )

        # Fallback directive if modules are empty
        if not directives:
            directives = [
                {
                    "agent_id": "campaign-agent",
                    "goal": plan.get("campaign_name", "Execute campaign"),
                    "prompt": f"Run campaign '{plan.get('campaign_name', 'Untitled')}'",
                    "capabilities": plan.get("tools_required", []),
                    "metadata": {"wizard_id": session.wizard_id},
                }
            ]

        # Call the real orchestrator
        orchestrator_base = resolve_env("GATEWAY_ORCHESTRATOR_URL", resolve_env("ORCHESTRATOR_URL", "http://localhost:10001"))
        url = f"{orchestrator_base}/v1/mao/start"
        payload = {
            "tenant": session.metadata.get("tenant") or resolve_env("TENANT_ID", "demo"),
            "initiator": session.user_id,
            "directives": directives,
            "metadata": {
                "wizard_session": session.session_id,
                "wizard_id": session.wizard_id,
                "campaign_name": plan.get("campaign_name"),
                "launch_date": plan.get("launch_date"),
            },
        }

        # Optional cost gating: attempt precheck if cost params present in answers
        budget_cap = session.answers.get("budget_cap") or session.metadata.get("budget_cap")
        hours_planned = session.answers.get("hours") or session.answers.get("hours_planned")
        gpu_model = session.answers.get("gpu_model")
        if budget_cap and hours_planned:
            pricing_service = resolve_env("PRICING_SERVICE_URL", "http://pricing-service:10026")
            precheck_url = f"{pricing_service}/v1/pricing/evaluate-budget/with-policy"
            pre_params = {
                "budget_cap": budget_cap,
                "hours_planned": hours_planned,
                "quantity": 1,
            }
            if gpu_model:
                pre_params["gpu_model"] = gpu_model
            try:
                pc_resp = requests.post(precheck_url, params=pre_params, timeout=10)
            except Exception as exc:
                logger.error("Pricing precheck request failed: %s", exc)
                raise RuntimeError("Pricing precheck failed; cannot approve execution") from exc

            if pc_resp.status_code != 200:
                logger.error("Pricing precheck non-200 response: %s - %s", pc_resp.status_code, pc_resp.text)
                raise RuntimeError("Pricing precheck unavailable; cannot approve execution")

            pc_data = pc_resp.json()
            decision = BudgetPrecheckDecision.model_validate(pc_data)
            if not decision.within_budget:
                return {
                    "status": "blocked",
                    "reason": decision.reason or "budget_exceeded",
                    "details": decision.model_dump(),
                }

        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code >= 400:
            raise RuntimeError(f"Orchestrator error: {resp.text}")

        data = resp.json()

        # Emit wizard approved event using outbox pattern
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        import asyncio

        async def emit_wizard_approved_event():
            event_data = {
                "wizard_id": session.wizard_id,
                "project_id": session.metadata.get("project_id", "default-project"),
                "user_id": session.user_id,
                "wizard_type": session.wizard_id,
                "configuration": {
                    "campaign_name": plan.get("campaign_name"),
                    "session_id": session_id,
                    "workflow_id": data.get("workflow_id"),
                    "answers": session.answers,
                    "metadata": session.metadata,
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Create outbox event
            engine = create_async_engine(resolve_env("DATABASE_URL", "sqlite+aiosqlite:///gateway.db"))
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

            async with async_session() as db_session:
                repo = OutboxEventRepository(session=db_session)
                await repo.save_event(event_type="wizard.approved.v1", event_data=event_data)
                await db_session.commit()

            await engine.dispose()
            logger.info(f"Wizard approved event persisted: {event_data}")

        # Emit event asynchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in a running event loop, use create_task
                loop.create_task(emit_wizard_approved_event())
            else:
                # Otherwise run it
                asyncio.run(emit_wizard_approved_event())
        except Exception as e:
            logger.error(f"Failed to emit wizard approved event: {e}")

        return {
            "status": "approved",
            "session_id": session_id,
            "execution_status": "queued",
            "message": "Campaign automation queued via Orchestrator",
            "workflow_id": data.get("workflow_id"),
            "orchestration_id": data.get("orchestration_id"),
            "task_queue": data.get("task_queue"),
            "estimated_completion": (datetime.now(UTC) + timedelta(hours=4)).isoformat(),
        }


# Global wizard engine instance
wizard_engine = WizardEngine()
