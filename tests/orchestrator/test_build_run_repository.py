import uuid
from sqlmodel import SQLModel, create_engine, Session

from services.orchestrator.app.repository.models import BuildRun
from services.orchestrator.app.repository.sql_build_run_repository import (
SQLBuildRunRepository,
)


def _setup_db():
engine = create_engine("sqlite:///:memory:")
SQLModel.metadata.create_all(engine)
return engine


def test_build_run_repository_crud():
engine = _setup_db()
with Session(engine) as session:
repo = SQLBuildRunRepository(session)
br = BuildRun(
tenant="demo",
project_id="proj-1",
pricing_snapshot_id="snap-1",
budget_cap=100.0,
estimated_cost=42.5,
template_set="default",
policy_reason="",
)
created = repo.create(br)
assert created.id is not None
fetched = repo.get(created.id)
assert fetched is not None
assert fetched.project_id == "proj-1"
assert fetched.estimated_cost == 42.5
