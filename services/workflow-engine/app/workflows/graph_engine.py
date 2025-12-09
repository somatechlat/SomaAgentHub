"""
Graph Workflow Engine - Handles GraphWorkflow execution via Temporal
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

from services.common.models.workflow import GraphWorkflow, WorkflowNode, NodeType

logger = logging.getLogger(__name__)


class GraphWorkflowEngine:
    """Graph workflow engine implementation"""

    def __init__(self):
        self.client = None
        self.worker = None
        self.active_workflows = (
            {}
        )  # In-memory cache of active workflow metadata (could be Redis/DB in prod)

    async def initialize(self):
        """Initialize temporal client and worker"""
        try:
            self.client = await Client.connect("localhost:7233")

            # Start worker for graph workflows
            from ..activities.graph_activities import GraphActivities
            from ..activities.hitl_activities import HITLActivities
            from ..activities.agent_activities import AgentActivities
            from ..activities.tool_activities import ToolActivities
            from ..activities.advanced_activities import AdvancedActivities
            from ..activities.rl_activities import RLActivities

            self.graph_activities = GraphActivities()
            self.hitl_activities = HITLActivities()
            self.agent_activities = AgentActivities()
            self.tool_activities = ToolActivities()
            self.advanced_activities = AdvancedActivities()
            self.rl_activities = RLActivities()

            task_queue = "graph-workflow-queue"
            self.worker = Worker(
                self.client,
                task_queue=task_queue,
                workflows=[GraphWorkflowDef],
                activities=[
                    self.graph_activities.save_checkpoint,
                    self.graph_activities.load_checkpoint,
                    self.graph_activities.record_node_execution_start,
                    self.graph_activities.record_node_execution_end,
                    self.hitl_activities.create_human_review_session,
                    self.hitl_activities.get_human_review_status,
                    self.agent_activities.execute_agent,
                    self.tool_activities.execute_tool,
                    self.advanced_activities.log_audit_event,
                    self.advanced_activities.retrieve_memory_context,
                    self.advanced_activities.store_memory_experience,
                    self.advanced_activities.fetch_capsule,
                    self.rl_activities.record_trajectory_step,
                    self.rl_activities.finalize_trajectory,
                ],
            )

            asyncio.create_task(self.worker.run())
            logger.info("Graph workflow engine initialized")

        except Exception as e:
            logger.error(f"Failed to initialize graph workflow engine: {e}")
            raise

    async def start_workflow(
        self, workflow_request: Dict[str, Any], tenant_context: Any
    ) -> Dict[str, Any]:
        """Start graph workflow"""

        # Validate request against GraphWorkflow model
        # Assuming workflow_request contains the definition or ID
        # For now, expect full definition in request for simplicity or ID to load

        workflow_id = str(uuid.uuid4())

        try:
            # Start temporal workflow
            handle = await self.client.start_workflow(
                GraphWorkflowDef.run,
                workflow_request,
                id=workflow_id,
                task_queue="graph-workflow-queue",
            )

            # Store workflow metadata
            self.active_workflows[workflow_id] = {
                "workflow_id": workflow_id,
                "workflow_type": "graph",
                "tenant_id": tenant_context.tenant_id,
                "status": "running",
                "started_at": datetime.utcnow(),
                "workflow_request": workflow_request,
                "handle": handle,
            }

            return {
                "workflow_id": workflow_id,
                "estimated_duration": 0,  # Real calculation needed
                "resource_allocation": {},
            }

        except Exception as e:
            logger.error(f"Failed to start graph workflow: {e}")
            raise

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get graph workflow status"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow_meta = self.active_workflows[workflow_id]

        try:
            description = await workflow_meta["handle"].describe()

            status = {
                "workflow_id": workflow_id,
                "workflow_type": "graph",
                "status": description.status.name,
                "started_at": workflow_meta["started_at"],
                "tenant_id": workflow_meta["tenant_id"],
            }

            if description.result:
                status["result"] = description.result

            return status

        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {
                "workflow_id": workflow_id,
                "workflow_type": "graph",
                "status": "error",
                "error": str(e),
            }

    async def list_workflows(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List graph workflows for tenant"""
        workflows = []
        for workflow_id, meta in self.active_workflows.items():
            if meta["tenant_id"] == tenant_id:
                workflows.append(await self.get_workflow_status(workflow_id))
        return workflows

    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel graph workflow"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        try:
            await self.active_workflows[workflow_id]["handle"].cancel()
            self.active_workflows[workflow_id]["status"] = "cancelled"
            return {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "cancelled_at": datetime.utcnow(),
            }
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            raise

    async def has_workflow(self, workflow_id: str) -> bool:
        return workflow_id in self.active_workflows


@workflow.defn
class GraphWorkflowDef:
    """Temporal Workflow definition for GraphWorkflow"""

    def __init__(self):
        self._pending_review_action = None

    @workflow.signal
    async def human_review_action(self, action: Dict[str, Any]):
        """Signal handler for human review actions"""
        # action should contain {"session_id": "...", "decision": "APPROVED"|"REJECTED"}
        self._pending_review_action = action

    @workflow.run
    async def run(self, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        workflow.logger.info(f"Starting graph workflow: {workflow_request}")

        workflow_id = workflow_request.get("id")
        graph_def = workflow_request.get("graph_def")
        initial_state = workflow_request.get("initial_state", {})

        return await self.execute_graph(workflow_id, graph_def, initial_state)

    async def execute_graph(
        self, workflow_id: str, graph_def: Dict[str, Any], initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        nodes = graph_def.get("nodes", [])
        edges = graph_def.get("edges", [])

        adj = {node["id"]: [] for node in nodes}
        in_degree = {node["id"]: 0 for node in nodes}
        node_map = {node["id"]: node for node in nodes}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in adj and target in in_degree:
                adj[source].append(target)
                in_degree[target] += 1

        # Find initial nodes (in-degree 0)
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        results = {}

        while queue:
            # Execute current layer in parallel
            current_layer = queue
            queue = []

            pending_tasks = []
            for node_id in current_layer:
                node = node_map[node_id]
                # Pass initial_state as input (simplification for now)
                node_input = initial_state.copy()
                pending_tasks.append(self._execute_node(workflow_id, node, node_input))

            # Wait for all tasks in this layer to complete
            layer_results = await asyncio.gather(*pending_tasks)

            for i, node_id in enumerate(current_layer):
                result = layer_results[i]
                results[node_id] = result

                # Check for failure
                if isinstance(result, dict) and result.get("status") == "failed":
                    return {
                        "status": "failed",
                        "reason": f"Node {node_id} failed",
                        "results": results,
                    }

                # Update neighbors
                for neighbor in adj[node_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return {"status": "completed", "results": results}

    async def _execute_node(
        self, workflow_id: str, node: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Any:
        node_type = node.get("type")
        node_id = node.get("id")
        tenant_id = node.get("metadata", {}).get("tenant_id")  # Ensure this is passed

        workflow.logger.info(f"Executing node {node_id} of type {node_type}")

        # 1. Record Start
        try:
            execution_id = await workflow.execute_activity(
                "record_node_execution_start",
                args=[workflow_id, node_id, input_data, tenant_id],
                start_to_close_timeout=timedelta(seconds=10),
            )
        except Exception as e:
            workflow.logger.error(f"Failed to record execution start: {e}")
            execution_id = None

        result = None
        error = None
        status = "SUCCEEDED"

        try:
            # Fetch Capsule if defined
            capsule_spec = None
            capsule_ref = node.get("metadata", {}).get(
                "capsule"
            )  # Expected format: "name:version"
            if capsule_ref and ":" in capsule_ref:
                c_name, c_ver = capsule_ref.split(":")
                try:
                    capsule_spec = await workflow.execute_activity(
                        "fetch_capsule",
                        args=[c_name, c_ver],
                        start_to_close_timeout=timedelta(seconds=10),
                    )
                except Exception as e:
                    workflow.logger.error(f"Failed to fetch capsule {capsule_ref}: {e}")
                    pass

            if node_type == "human_interrupt":
                # Create review session
                session_id = await workflow.execute_activity(
                    "create_human_review_session",
                    args=[
                        workflow_id,
                        node_id,
                        {"context": f"Review required for {node_id}"},
                    ],
                    start_to_close_timeout=timedelta(hours=24),
                )

                # Wait for signal
                workflow.logger.info(
                    f"Waiting for human review on session {session_id}"
                )
                await workflow.wait_condition(
                    lambda: self._pending_review_action is not None
                )

                action = self._pending_review_action
                decision = action.get("decision")
                workflow.logger.info(f"Received human review decision: {decision}")

                self._pending_review_action = None  # Reset

                if decision == "REJECTED":
                    status = "FAILED"
                    error = {"reason": "Human rejected"}
                    result = {"status": "failed", "reason": "Human rejected"}
                else:
                    result = {
                        "status": "completed",
                        "decision": decision,
                        "session_id": session_id,
                    }

            elif node_type == "agent":
                # Execute real agent activity via Role System
                workflow.logger.info(f"Calling execute_agent for {node_id}")

                role_id = node.get("metadata", {}).get("role_id")
                if not role_id:
                    role_id = node.get("metadata", {}).get("agent_id", node_id)

                # Prepare context
                exec_context = {
                    "tenant_id": tenant_id,
                    "workflow_instance_id": workflow_id,
                    "node_execution_id": execution_id,
                }

                # Retrieve context from memory
                context_docs = await workflow.execute_activity(
                    "retrieve_memory_context",
                    args=[role_id, str(input_data), 5, exec_context],
                    start_to_close_timeout=timedelta(seconds=10),
                )

                # Enrich input
                input_data["memory_context"] = context_docs
                if capsule_spec:
                    input_data["capsule_spec"] = capsule_spec

                input_data["tenant_id"] = tenant_id
                input_data["workflow_instance_id"] = workflow_id
                input_data["node_execution_id"] = execution_id

                agent_result = await workflow.execute_activity(
                    "execute_agent",
                    args=[role_id, input_data],
                    start_to_close_timeout=timedelta(minutes=5),
                )

                # Store experience
                await workflow.execute_activity(
                    "store_memory_experience",
                    args=[
                        role_id,
                        str(agent_result.get("output")),
                        {"workflow_id": workflow_id, "node_id": node_id},
                        exec_context,
                    ],
                    start_to_close_timeout=timedelta(seconds=10),
                )

                # Audit Log
                await workflow.execute_activity(
                    "log_audit_event",
                    args=[
                        "agent.execution",
                        role_id,
                        "execute",
                        node_id,
                        "success",
                        {"result": str(agent_result)},
                    ],
                    start_to_close_timeout=timedelta(seconds=10),
                )

                # RL Trajectory Recording
                # Check if this workflow is part of an RL pipeline (flag passed in input or metadata)
                # For now, we check if 'reasoning_pipeline_id' is in input_data or workflow metadata
                # We need access to workflow-level metadata here.
                # Assuming input_data contains it or we pass it.
                # Let's assume input_data has 'rl_context' if applicable.
                rl_context = input_data.get("rl_context")
                if rl_context:
                    try:
                        step_data = {
                            "observation": input_data.get("content"),  # Simplified
                            "action": agent_result.get("output"),
                            "reward": 0.0,  # Placeholder, reward calc happens later or via signal
                        }
                        await workflow.execute_activity(
                            "record_trajectory_step",
                            args=[workflow_id, node_id, role_id, step_data, rl_context],
                            start_to_close_timeout=timedelta(seconds=10),
                        )
                    except Exception as e:
                        workflow.logger.error(f"Failed to record trajectory step: {e}")

                result = {"status": "completed", "agent_result": agent_result}

            elif node_type == "tool":
                # Execute real tool activity
                workflow.logger.info(f"Calling execute_tool for {node_id}")

                tool_spec = node.get("parameters", {})
                if "id" not in tool_spec:
                    tool_spec["id"] = node.get("toolId", node_id)

                if capsule_spec:
                    tool_spec["capsule_spec"] = capsule_spec
                # Arguments from input or context
                arguments = {
                    "context": node,
                    "timestamp": str(workflow.now()),
                    "workflow_instance_id": workflow_id,
                    "node_execution_id": execution_id,
                }
                # Also pass input_data as arguments for the tool itself
                arguments.update(input_data)

                tool_result = await workflow.execute_activity(
                    "execute_tool",
                    args=[tool_spec, arguments],
                    start_to_close_timeout=timedelta(minutes=1),
                )

                result = {"status": "completed", "type": "tool", "result": tool_result}

            else:
                status = "SKIPPED"
                result = {"status": "skipped", "reason": "unknown_type"}

        except Exception as e:
            workflow.logger.error(f"Node execution failed: {e}")
            status = "FAILED"
            error = {"message": str(e)}
            result = {"status": "failed", "error": str(e)}

        # 2. Record End
        if execution_id:
            try:
                await workflow.execute_activity(
                    "record_node_execution_end",
                    args=[execution_id, status, result, error],
                    start_to_close_timeout=timedelta(seconds=10),
                )
            except Exception as e:
                workflow.logger.error(f"Failed to record execution end: {e}")

        # Checkpoint
        try:
            await workflow.execute_activity(
                "save_checkpoint",
                args=[
                    workflow_id,
                    node_id,
                    {
                        "status": status,
                        "timestamp": str(workflow.now()),
                        "result": result,
                    },
                ],
                start_to_close_timeout=timedelta(seconds=10),
            )
        except Exception as e:
            workflow.logger.error(f"Failed to save checkpoint: {e}")

        return result
