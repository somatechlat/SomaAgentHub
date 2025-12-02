#!/usr/bin/env python3
"""
Fix partial indentation in Python files.

This script handles cases where the file header (docstring) is at indent 0,
but the actual code (imports, classes, functions) is indented.
It finds the first 'code line' and unindents the whole file by that amount.
"""

import re
import sys
from pathlib import Path

# Regex to identify "code lines" that should definitely be at top level
CODE_START_RE = re.compile(r"^\s*(import |from |class |def |@)")


def fix_file(file_path: Path) -> bool:
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return False

    # Find indentation of first code line
    shift_amount = 0
    found_code = False

    for line in lines:
        if not line.strip():
            continue

        # If we hit a code line, check its indent
        if CODE_START_RE.match(line):
            indent = len(line) - len(line.lstrip())
            if indent > 0:
                shift_amount = indent
                found_code = True
            break

        # If we hit something else that is NOT a docstring/comment (hard to tell perfectly),
        # we might stop. But usually docstrings start with " or #.
        # Let's just look for the FIRST code line regardless of what came before.

    if shift_amount == 0:
        return False

    print(f"Fixing {file_path}: Unindenting by {shift_amount} spaces...")

    new_lines = []
    for line in lines:
        if not line.strip():
            new_lines.append(line)
            continue

        # Unindent
        if len(line) >= shift_amount:
            new_lines.append(line[shift_amount:])
        else:
            new_lines.append(line.lstrip())

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"Error writing {file_path}: {e}", file=sys.stderr)
        return False


        def main():
    repo_root = Path(__file__).parent.parent
    print(f"Scanning {repo_root} for partially indented files...")

    python_files = list(repo_root.glob("**/*.py"))

    fixed_count = 0
    for py_file in python_files:
        if any(part.startswith(".") or part == "venv" for part in py_file.parts):
            continue

        if fix_file(py_file):
            fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")


    if __name__ == "__main__":
    main()
