import pytest
from temporalio import workflow
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

@workflow.defn
class SimpleWorkflow:
    @workflow.run
    async def run(self) -> str:
        return "Hello, World!"

@pytest.mark.asyncio
async def test_simple_workflow():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[SimpleWorkflow],
        ) as worker:
            result = await env.client.execute_workflow(
                SimpleWorkflow.run,
                id="test-simple",
                task_queue="test-queue",
            )
            assert result == "Hello, World!"
