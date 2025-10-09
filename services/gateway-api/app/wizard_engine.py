"""Wizard Engine - Interactive project setup and campaign creation."""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid


class WizardQuestion(BaseModel):
    """Individual wizard question definition."""
    id: str
    step: int
    prompt: str
    type: str  # text, select, multi_select, date, boolean, number, etc.
    required: bool = True
    options: Optional[List[Dict[str, Any]]] = None
    default: Optional[Any] = None
    placeholder: Optional[str] = None
    help: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


class WizardSession(BaseModel):
    """Active wizard session state."""
    session_id: str
    wizard_id: str
    user_id: str
    current_step: int = 1
    answers: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WizardModule(BaseModel):
    """Execution module after wizard completion."""
    id: str
    title: str
    agent: str
    dependencies: List[str]
    tasks: List[Dict[str, Any]]
    outputs: List[str]
    status: str = "pending"  # pending, in_progress, completed, failed


class WizardEngine:
    """Core wizard engine for interactive project setup."""
    
    def __init__(self):
        self.wizards_path = Path(__file__).parent / "wizards"
        self.sessions: Dict[str, WizardSession] = {}
        self.wizard_schemas: Dict[str, Dict] = {}
        self._load_wizard_schemas()
    
    def _load_wizard_schemas(self):
        """Load all wizard YAML schemas from the wizards directory."""
        if not self.wizards_path.exists():
            return
        
        for yaml_file in self.wizards_path.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    schema = yaml.safe_load(f)
                    wizard_id = schema.get('wizard_id')
                    if wizard_id:
                        self.wizard_schemas[wizard_id] = schema
            except Exception as e:
                print(f"Error loading wizard schema {yaml_file}: {e}")
    
    def list_wizards(self) -> List[Dict[str, Any]]:
        """List all available wizards."""
        return [
            {
                "wizard_id": wiz_id,
                "title": schema.get("title"),
                "description": schema.get("description"),
                "version": schema.get("version"),
                "estimated_duration": schema.get("estimated_duration", {}).get("total")
            }
            for wiz_id, schema in self.wizard_schemas.items()
        ]
    
    def start_wizard(self, wizard_id: str, user_id: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Start a new wizard session."""
        if wizard_id not in self.wizard_schemas:
            raise ValueError(f"Wizard '{wizard_id}' not found")
        
        session_id = f"wiz-{uuid.uuid4().hex[:12]}"
        session = WizardSession(
            session_id=session_id,
            wizard_id=wizard_id,
            user_id=user_id,
            metadata=metadata or {}
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
            "progress": self._calculate_progress(session)
        }
    
    def _get_current_question(self, session: WizardSession) -> Optional[Dict[str, Any]]:
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
                    "help": q.get("help")
                }
        
        return None
    
    def submit_answer(self, session_id: str, answer: Dict[str, Any]) -> Dict[str, Any]:
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
            "completed": False
        }
    
    def _calculate_progress(self, session: WizardSession) -> Dict[str, Any]:
        """Calculate wizard completion progress."""
        schema = self.wizard_schemas[session.wizard_id]
        total_steps = len(schema.get("questions", []))
        completed_steps = session.current_step - 1
        
        return {
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "percentage": int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
        }
    
    def _complete_wizard(self, session: WizardSession) -> Dict[str, Any]:
        """Complete wizard and prepare execution plan."""
        schema = self.wizard_schemas[session.wizard_id]
        
        # Build execution plan
        modules = []
        for module_def in schema.get("modules", []):
            module = WizardModule(
                id=module_def["id"],
                title=module_def["title"],
                agent=module_def["agent"],
                dependencies=module_def.get("dependencies", []),
                tasks=module_def.get("tasks", []),
                outputs=module_def.get("outputs", [])
            )
            modules.append(module.dict())
        
        # Interpolate answers into tasks
        execution_plan = self._build_execution_plan(session, modules)
        
        return {
            "session_id": session.session_id,
            "completed": True,
            "progress": {"completed_steps": session.current_step, "total_steps": session.current_step, "percentage": 100},
            "summary": {
                "wizard_id": session.wizard_id,
                "wizard_title": schema.get("title"),
                "answers": session.answers,
                "started_at": session.started_at.isoformat(),
                "completed_at": datetime.utcnow().isoformat()
            },
            "execution_plan": execution_plan,
            "next_steps": {
                "action": "approve_and_execute",
                "message": "Review the execution plan and approve to start the campaign automation",
                "endpoints": {
                    "approve": f"/v1/wizard/{session.session_id}/approve",
                    "modify": f"/v1/wizard/{session.session_id}/modify"
                }
            }
        }
    
    def _build_execution_plan(self, session: WizardSession, modules: List[Dict]) -> Dict[str, Any]:
        """Build detailed execution plan from wizard answers."""
        schema = self.wizard_schemas[session.wizard_id]
        
        # Interpolate variables
        def interpolate(text: str) -> str:
            """Replace {variable} with actual answers."""
            if not isinstance(text, str):
                return text
            result = text
            for key, value in session.answers.items():
                result = result.replace(f"{{{key}}}", str(value))
            return result
        
        # Process modules with interpolation
        processed_modules = []
        for module in modules:
            processed = module.copy()
            processed["title"] = interpolate(module["title"])
            
            # Interpolate task descriptions and params
            processed_tasks = []
            for task in module.get("tasks", []):
                processed_task = {
                    "action": task["action"],
                    "description": interpolate(task.get("description", "")),
                    "params": {}
                }
                
                # Interpolate params
                for key, value in task.get("params", {}).items():
                    if isinstance(value, list):
                        # Handle variable references like {channels}
                        processed_task["params"][key] = [
                            session.answers.get(v.strip("{}"), v) if isinstance(v, str) and v.startswith("{") else v
                            for v in value
                        ]
                    else:
                        processed_task["params"][key] = interpolate(str(value)) if isinstance(value, str) else value
                
                processed_tasks.append(processed_task)
            
            processed["tasks"] = processed_tasks
            processed_modules.append(processed)
        
        return {
            "plan_id": f"plan-{session.session_id}",
            "campaign_name": session.answers.get("campaign_name", "Untitled Campaign"),
            "launch_date": session.answers.get("launch_date"),
            "modules": processed_modules,
            "estimated_duration": schema.get("estimated_duration", {}).get("total"),
            "agents_required": list(set(m["agent"] for m in modules)),
            "tools_required": self._extract_required_tools(processed_modules),
            "success_criteria": schema.get("success_criteria", {})
        }
    
    def _extract_required_tools(self, modules: List[Dict]) -> List[str]:
        """Extract unique list of tools required for execution."""
        tools = set()
        for module in modules:
            for task in module.get("tasks", []):
                action = task.get("action", "")
                if "." in action:
                    tool = action.split(".")[0]
                    tools.add(tool)
        return sorted(list(tools))
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
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
            "progress": self._calculate_progress(session)
        }
    
    def approve_execution(self, session_id: str) -> Dict[str, Any]:
        """Approve wizard execution plan and trigger real orchestration via Orchestrator."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found")

        if not session.completed:
            raise ValueError("Wizard must be completed before approval")

        # Build a minimal multi-agent orchestration request from the execution plan
        plan = self._build_execution_plan(session, [])
        directives: List[Dict[str, Any]] = []
        for module in plan.get("modules", []):
            directives.append(
                {
                    "agent_id": module.get("agent", module.get("id", "agent")),
                    "goal": module.get("title", "Execute module"),
                    "prompt": module.get("title", "Execute tasks"),
                    "capabilities": list({t.get("action", "").split(".")[0] for t in module.get("tasks", []) if t.get("action")}),
                    "metadata": {"module_id": module.get("id")},
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
        import os
        import requests
        orchestrator_base = os.getenv("SOMAGENT_GATEWAY_ORCHESTRATOR_URL", "http://orchestrator:1004")
        url = f"{orchestrator_base}/v1/mao/start"
        payload = {
            "tenant": session.metadata.get("tenant", "demo"),
            "initiator": session.user_id,
            "directives": directives,
            "metadata": {"wizard_session": session.session_id, "wizard_id": session.wizard_id},
        }

        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code >= 400:
            raise RuntimeError(f"Orchestrator error: {resp.text}")

        data = resp.json()
        return {
            "status": "approved",
            "session_id": session_id,
            "execution_status": "queued",
            "message": "Campaign automation queued via Orchestrator",
            "workflow_id": data.get("workflow_id"),
            "orchestration_id": data.get("orchestration_id"),
            "task_queue": data.get("task_queue"),
            "estimated_completion": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
        }


# Global wizard engine instance
wizard_engine = WizardEngine()
