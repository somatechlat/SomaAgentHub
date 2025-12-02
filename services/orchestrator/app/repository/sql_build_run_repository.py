from __future__ import annotations

import uuid

from sqlmodel import Session, select

from .interfaces import BuildRunRepository
from .models import BuildRun


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
