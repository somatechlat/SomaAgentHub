"""Capsule loader utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

from .config import get_settings


class CapsuleLoader:
    """Loads capsule definitions from YAML files on disk."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self._cache: Dict[str, dict] = {}

    def load_all(self) -> List[dict]:
        capsules = []
        for path in sorted(self.base_path.glob("*.yml")) + sorted(self.base_path.glob("*.yaml")):
            capsule = self._load_file(path)
            if capsule:
                capsules.append(capsule)
        return capsules

    def load_one(self, capsule_id: str) -> dict | None:
        if capsule_id in self._cache:
            return self._cache[capsule_id]
        for path in self.base_path.glob("*.yml"):
            if path.stem == capsule_id:
                return self._load_file(path)
        for path in self.base_path.glob("*.yaml"):
            if path.stem == capsule_id:
                return self._load_file(path)
        return None

    def _load_file(self, path: Path) -> dict | None:
        try:
            data = yaml.safe_load(path.read_text())
        except Exception:  # noqa: BLE001
            return None
        if not isinstance(data, dict):
            return None
        capsule_id = data.get("id") or path.stem
        data.setdefault("id", capsule_id)
        self._cache[capsule_id] = data
        return data


_loader: CapsuleLoader | None = None


def get_loader() -> CapsuleLoader:
    global _loader
    if _loader is None:
        settings = get_settings()
        base = Path(__file__).resolve().parent.parent / settings.capsule_dir
        _loader = CapsuleLoader(base)
    return _loader
