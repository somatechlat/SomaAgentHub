from __future__ import annotations

import uuid
from typing import Protocol

from ..repository.models import BuildRun


class BuildRunRepository(Protocol):
    def create(self, br: BuildRun) -> BuildRun: ...

    def get(self, build_run_id: uuid.UUID) -> BuildRun | None: ...
