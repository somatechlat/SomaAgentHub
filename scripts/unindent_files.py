#!/usr/bin/env python3
"""
Unindent globally indented Python files.

This script fixes files where the entire content (including imports and class definitions)
is indented by some amount. It finds the minimum indentation of non-empty lines
and shifts the whole file left.
"""

import sys
from pathlib import Path


def unindent_file(file_path: Path) -> bool:
    """
    Unindent a globally indented Python file.
    Returns True if modified.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return False

    # Find minimum indentation of non-empty lines
    min_indent = 1000
    has_content = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        has_content = True
        indent = len(line) - len(line.lstrip())
        if indent < min_indent:
            min_indent = indent

    if not has_content or min_indent == 0 or min_indent == 1000:
        return False

    print(f"Unindenting {file_path} by {min_indent} spaces...")

    new_lines = []
    for line in lines:
        if not line.strip():
            new_lines.append(line)
            continue

        # Remove min_indent characters from start
        # Be careful not to slice more than exists (though logic says it shouldn't happen)
        if len(line) >= min_indent:
            new_lines.append(line[min_indent:])
        else:
            new_lines.append(line.lstrip())  # Fallback

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"Error writing {file_path}: {e}", file=sys.stderr)
        return False


        def main():
    repo_root = Path(__file__).parent.parent
    print(f"Scanning {repo_root} for globally indented files...")

    python_files = list(repo_root.glob("**/*.py"))

    fixed_count = 0
    for py_file in python_files:
        if any(part.startswith(".") or part == "venv" for part in py_file.parts):
            continue

        if unindent_file(py_file):
            fixed_count += 1

    print(f"\nTotal files unindented: {fixed_count}")


    if __name__ == "__main__":
    main()
