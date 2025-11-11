from __future__ import annotations

import uuid
from typing import Any

from sqlmodel import Session, select

from .models import BuildRun
from .interfaces import BuildRunRepository
from services.common.config.base_settings import resolve_env


class SQLBuildRunRepository(BuildRunRepository):
def __init__(self, session: Session):
self._session = session

def create(self, br: BuildRun) -> BuildRun:
self._session.add(br)
self._session.commit()
self._session.refresh(br)
return br

def get(self, build_run_id: uuid.UUID) -> BuildRun | None:
stmt = select(BuildRun).where(BuildRun.id == build_run_id)
return self._session.exec(stmt).first()
