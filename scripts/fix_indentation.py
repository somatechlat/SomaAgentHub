#!/usr/bin/env python3
"""
Fix systematic indentation errors in Python files.

This script fixes a specific pattern where lines that should be indented
(after colons, inside functions/classes) have zero indentation.

It uses a heuristic approach based on colons and previous indentation levels.
"""

import sys
from pathlib import Path


def fix_indentation(file_path: Path) -> bool:
    """
    Fix missing indentation in a Python file.

    Returns True if file was modified, False otherwise.
    """
    # Skip this script itself to avoid self-modification issues
    if file_path.name == "fix_indentation.py":
        return False

    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return False

    modified = False
    new_lines = []

    # State tracking
    expected_indent = 0
    indent_stack = [0]  # Keep track of indentation levels

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines, but preserve them
        if not stripped:
            new_lines.append(line)
            continue

        # Calculate current indentation
        current_indent = len(line) - len(line.lstrip())

        # Heuristic: If we expect indentation but found none (and it's not a comment)
        if expected_indent > 0 and current_indent == 0 and not stripped.startswith("#"):
            # Apply expected indentation
            line = " " * expected_indent + line
            current_indent = expected_indent
            modified = True

        # Update state for NEXT line
        if stripped.endswith(":"):
            # We just opened a block, expect more indentation next
            expected_indent = current_indent + 4
            indent_stack.append(expected_indent)
        else:
            # If we are not opening a block, we might be closing one or staying same.
            # This is hard to know for sure without full parsing, but for the specific
            # "stripped indentation" error, we usually just need to maintain level
            # until we see a dedent (which we can't easily detect without context).
            #
            # However, if the line IS indented, we should trust it and update our expectation.
            if current_indent > 0:
                expected_indent = current_indent
                # Adjust stack if needed (simplified)
                while indent_stack and indent_stack[-1] > current_indent:
                    indent_stack.pop()
                if not indent_stack or indent_stack[-1] < current_indent:
                    indent_stack.append(current_indent)

            # If we are at 0 indent and didn't just fix it, reset expectation
            elif current_indent == 0 and not modified:
                expected_indent = 0
                indent_stack = [0]

        new_lines.append(line)

    if modified:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}", file=sys.stderr)
            return False

    return False


def main():
    """Find and fix all Python files with indentation errors."""
    repo_root = Path(__file__).parent.parent

    print(f"Scanning {repo_root} for Python files...")

    # Find all Python files
    python_files = list(repo_root.glob("**/*.py"))

    fixed_count = 0
    for py_file in python_files:
        # Skip venv and hidden directories
        if any(part.startswith(".") or part == "venv" for part in py_file.parts):
            continue

        if fix_indentation(py_file):
            print(f"Fixed: {py_file.relative_to(repo_root)}")
            fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")


if __name__ == "__main__":
    main()
