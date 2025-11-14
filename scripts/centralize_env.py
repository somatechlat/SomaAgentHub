#!/usr/bin/env python3
"""Utility to replace raw ``os.getenv`` calls with ``resolve_env`` across the codebase.

It can run in **dry-run** mode, target specific directories, and skip third-party
paths. The default scope is ``services/**`` because runtime configuration must
conform to the shared resolver. Running this script from CI or a pre-commit hook
keeps the allowed env access centralized.
"""

from __future__ import annotations

import argparse
import logging
import pathlib
import re
from collections.abc import Iterable

BASE_IMPORT = "from services.common.config.base_settings import resolve_env"
OS_GETENV_RE = re.compile(r"os\.getenv\s*\(")


def _should_skip(path: pathlib.Path, excludes: Iterable[str]) -> bool:
if path.suffix != ".py":
return True
for part in path.parts:
if part in {"venv", ".venv", "build", "dist", "__pycache__"}:
return True
for pattern in excludes:
if path.match(pattern):
return True
return False


def _process_file(path: pathlib.Path, dry_run: bool) -> bool:
original = path.read_text()
transformed = OS_GETENV_RE.sub("resolve_env(", original)
if BASE_IMPORT not in transformed:
lines = transformed.splitlines()
insert_idx = 0
for i, line in enumerate(lines):
stripped = line.strip()
if stripped.startswith(("import ", "from ")):
insert_idx = i + 1
lines.insert(insert_idx, BASE_IMPORT)
transformed = "\n".join(lines) + "\n"
if transformed == original:
return False
if dry_run:
logging.info("Would update %s", path)
return True
path.write_text(transformed)
logging.info("Updated %s", path)
return True


def _iter_paths(
root: pathlib.Path, includes: Iterable[str], excludes: Iterable[str]
) -> Iterable[pathlib.Path]:
seen: set[pathlib.Path] = set()
for pattern in includes:
resolved = (
root / pattern
if not pathlib.Path(pattern).is_absolute()
else pathlib.Path(pattern)
)
if resolved.is_dir():
for candidate in resolved.rglob("*.py"):
if candidate not in seen and not _should_skip(candidate, excludes):
    seen.add(candidate)
    yield candidate
else:
for candidate in resolved.glob("*"):
if (
    candidate not in seen
    and candidate.is_file()
    and candidate.suffix == ".py"
    and not _should_skip(candidate, excludes)
):
    seen.add(candidate)
    yield candidate


def main(argv: list[str] | None = None) -> None:
parser = argparse.ArgumentParser(
description="Centralize env access with resolve_env"
)
parser.add_argument(
"--dry-run",
action="store_true",
help="Report files that would change without writing them.",
)
parser.add_argument(
"--include",
action="append",
default=["services"],
help="Glob or directory to include (default: services).",
)
parser.add_argument(
"--exclude",
action="append",
default=[],
help="Glob or path pattern to skip (can be given multiple times).",
)
parser.add_argument(
"--root",
default=".",
help="Repository root directory (default: current directory).",
)
args = parser.parse_args(argv)

root = pathlib.Path(args.root).resolve()
if not root.exists():
raise SystemExit(f"Root path {root} does not exist")

paths = list(_iter_paths(root, args.include, args.exclude))
modified = False
for path in paths:
modified |= _process_file(path, args.dry_run)

if not modified:
logging.info("No files required updates")


if __name__ == "__main__":
logging.basicConfig(level=logging.INFO, format="%(message)s")
main()
