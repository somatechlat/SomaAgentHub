#!/usr/bin/env python3
"""Utility to replace raw os.getenv calls with resolve_env across the codebase.
It scans all *.py files, replaces `resolve_env(` with `resolve_env(`, and ensures the
import `from services.common.config.base_settings import resolve_env` is present.
Backup files are removed beforehand (see parallel sprint)."""
import re, sys, pathlib, fileinput

BASE_IMPORT = "from services.common.config.base_settings import resolve_env"


def process_file(path: pathlib.Path):
    text = path.read_text()
    # Replace os.getenv with resolve_env
    new_text = re.sub(r"os\.getenv\s*\(", "resolve_env(", text)
    # Ensure import is present (skip if already imported)
    if BASE_IMPORT not in new_text:
        # Insert after any existing imports or at top
        lines = new_text.splitlines()
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_idx = i + 1
        lines.insert(insert_idx, BASE_IMPORT)
        new_text = "\n".join(lines) + "\n"
    if new_text != text:
        path.write_text(new_text)
        print(f"Updated {path}")


def main():
    root = pathlib.Path(__file__).parent.parent
    for py_file in root.rglob("*.py"):
        # Skip the virtual environment and other irrelevant directories
        if ".venv" in py_file.parts:
            continue
        # Skip generated files or third‑party packages if needed
        process_file(py_file)


if __name__ == "__main__":
    main()
