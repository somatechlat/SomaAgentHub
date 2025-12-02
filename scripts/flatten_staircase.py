#!/usr/bin/env python3
"""
Flatten "staircase" indentation in Python files.

This script fixes files where methods have been accidentally nested inside each other,
creating a deep staircase pattern. It resets all methods within a class to 4 spaces
and their bodies to 8 spaces.
"""

import re
import sys
from pathlib import Path


def flatten_file(file_path: Path) -> bool:
    """
    Flatten indentation in a Python file.
    Returns True if modified.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return False

    # Check if file needs flattening (has deep nesting of defs)
    has_deep_nesting = False
    for line in lines:
        if re.match(r"^\s{12,}def ", line) or re.match(r"^\s{12,}async def ", line):
            has_deep_nesting = True
            break

    if not has_deep_nesting:
        return False

    print(f"Flattening {file_path}...")

    new_lines = []
    in_class = False
    current_def_indent = 0
    body_shift = 0

    # Regex to detect class and def
    class_re = re.compile(r"^class\s+\w+")
    def_re = re.compile(r"^\s*(async\s+)?def\s+")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            new_lines.append(line)
            continue

        # Check for class start
        if class_re.match(line):
            in_class = True
            new_lines.append(line)
            continue

        # Check for method definition
        if in_class and def_re.match(line):
            # Force method to 4 spaces
            # Preserve the 'def ...' part
            content = line.lstrip()
            new_lines.append("    " + content)

            # Calculate how much we need to shift the body
            # The original body was indented relative to the ORIGINAL def line.
            # We want the new body to be at 8 spaces.
            # But wait, the lines following this def will be read in the loop.
            # We need to know the indentation of the NEXT line to calculate shift?
            # No, simpler: We assume the body IS indented relative to this def.
            # We just need to know that for all subsequent lines UNTIL the next def,
            # we want to force them to 8 spaces (or relative to 8).

            # Actually, the "Staircase" means:
            # def A:
            #     body A
            #     def B:
            #         body B
            #
            # We want:
            # def A:
            #     body A
            # def B:
            #     body B

            # So when we see `def`, we reset our "target base indent" to 8.
            continue

        # If we are in a class, and it's not a def, it's body code.
        if in_class:
            # We want to preserve relative indentation within the body,
            # but anchor the base to 8 spaces.
            # The problem is determining "relative".
            # In the broken files, indentation increases monotonically.
            #
            # Heuristic:
            # If it's a body line, just indent it to 8 spaces?
            # No, that destroys if/else blocks inside the method.
            #
            # Better Heuristic:
            # If we hit a `def`, we set a "current_def_indent" variable to the indentation of that def line.
            # For subsequent lines, we calculate `relative_indent = line_indent - current_def_indent`.
            # Then `new_indent = 4 + relative_indent`.
            # But wait, in the BROKEN file, `def B` is inside `def A`.
            # So `def B` has indent > `def A`.
            # If we treat `def B` as a top-level method (indent 4), we reset the calculation.
            pass

    # Let's try a second pass approach which is simpler:
    # 1. Identify all `def` lines. Force them to 4 spaces.
    # 2. For lines between `def` A and `def` B:
    #    Find the minimum indentation of non-empty lines in this block.
    #    Shift the whole block so that minimum indentation becomes 8.

    processed_lines = []

    # We need to process the file in chunks (methods).
    # But we also have class-level stuff (docstrings, fields).

    # Let's stick to the "Force def to 4" and "Shift body" strategy.

    # Pass 1: Identify split points (defs)
    # We will reconstruct the file.

    current_block = []

    # Helper to flush a block
    def flush_block(block_lines, is_method_body=False):
        if not block_lines:
            return []

        if not is_method_body:
            return block_lines

        # Find min indent
        min_indent = 1000
        for l in block_lines:
            if l.strip():
                ind = len(l) - len(l.lstrip())
                if ind < min_indent:
                    min_indent = ind

        if min_indent == 1000:
            return block_lines

        # Shift to 8 spaces
        shifted = []
        for l in block_lines:
            if not l.strip():
                shifted.append(l)
                continue

            current = len(l) - len(l.lstrip())
            relative = current - min_indent
            new_ind = 8 + relative
            shifted.append(" " * new_ind + l.lstrip())
        return shifted

    final_lines = []
    buffer = []

    # State
    seen_first_class = False

    for line in lines:
        if class_re.match(line):
            # Flush whatever was before class (imports etc)
            final_lines.extend(buffer)
            buffer = []
            final_lines.append(line)
            seen_first_class = True
            continue

        if not seen_first_class:
            buffer.append(line)
            continue

        # Inside class
        if def_re.match(line):
            # Flush previous body
            final_lines.extend(flush_block(buffer, is_method_body=True))
            buffer = []

            # Add the def line at 4 spaces
            final_lines.append("    " + line.lstrip())
        else:
            buffer.append(line)

    # Flush last buffer
    final_lines.extend(flush_block(buffer, is_method_body=True))

    # Write back
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(final_lines)
        return True
    except Exception as e:
        print(f"Error writing {file_path}: {e}", file=sys.stderr)
        return False


def main():
    repo_root = Path(__file__).parent.parent
    print(f"Scanning {repo_root} for staircase files...")

    # Use the grep command logic to find files, or just scan all
    # Scanning all is safer to ensure we catch everything
    python_files = list(repo_root.glob("**/*.py"))

    fixed_count = 0
    for py_file in python_files:
        if any(part.startswith(".") or part == "venv" for part in py_file.parts):
            continue

        if flatten_file(py_file):
            fixed_count += 1

    print(f"\nTotal files flattened: {fixed_count}")


if __name__ == "__main__":
    main()
