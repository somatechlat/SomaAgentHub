#!/usr/bin/env python3
"""
VIBE Coding Rules Auto-Remediation Script

This script automatically fixes common VIBE coding rules violations:
1. Replace print() with logging
2. Fix naive datetime.now() to datetime.now(UTC)
3. Generate TODO tracking issues
4. Report duplicate services

Usage:
    python scripts/fix_vibe_violations.py --check        # Dry run
    python scripts/fix_vibe_violations.py --fix-logging  # Fix print statements
    python scripts/fix_vibe_violations.py --fix-datetime # Fix datetime calls
    python scripts/fix_vibe_violations.py --list-todos   # List all TODOs
    python scripts/fix_vibe_violations.py --all          # Fix everything
"""

import argparse
import re
import subprocess
from pathlib import Path
from typing import Any

# ANSI colors for output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(msg: str) -> None:
    """Print colored header."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{msg}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(msg: str) -> None:
    """Print success message."""
    print(f"{GREEN}✅ {msg}{RESET}")


def print_error(msg: str) -> None:
    """Print error message."""
    print(f"{RED}❌ {msg}{RESET}")


def print_warning(msg: str) -> None:
    """Print warning message."""
    print(f"{YELLOW}⚠️  {msg}{RESET}")


def find_repo_root() -> Path:
    """Find the repository root directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    msg = "Not in a git repository"
    raise RuntimeError(msg)


def find_print_violations(
    dry_run: bool = True,  # noqa: FBT001, FBT002
) -> list[tuple[Path, int, str]]:
    """Find all print() statements in production code."""
    print_header("Finding print() violations")
    
    repo_root = find_repo_root()
    services_dir = repo_root / "services"
    violations = []
    
    # Exclude examples and tests from violation list
    exclude_patterns = {"examples/", "tests/", "conftest.py", "__pycache__"}
    
    for py_file in services_dir.rglob("*.py"):
        # Skip excluded paths
        if any(pattern in str(py_file) for pattern in exclude_patterns):
            continue
            
        try:
            with py_file.open() as f:
                for line_num, line in enumerate(f, 1):
                    # Match print( but not console.print or #print
                    if re.search(r"\bprint\s*\(", line) and not line.strip().startswith("#"):
                        violations.append((py_file, line_num, line.strip()))
        except (UnicodeDecodeError, PermissionError):
            continue
    
    print(f"Found {len(violations)} print() violations in production code\n")
    
    # Show first 10
    for file_path, line_num, line in violations[:10]:
        rel_path = file_path.relative_to(repo_root)
        print(f"  {rel_path}:{line_num}")
        print(f"    {line[:80]}...")
    
    if len(violations) > 10:
        print(f"\n  ... and {len(violations) - 10} more")
    
    return violations


def fix_print_statements(dry_run: bool = True) -> int:  # noqa: FBT001, FBT002
    """Replace print() with logger.info()."""
    print_header("Fixing print() statements" + (" [DRY RUN]" if dry_run else ""))
    
    violations = find_print_violations(dry_run)
    fixed = 0
    
    if not violations:
        print_success("No violations found!")
        return 0
    
    if dry_run:
        print_warning(f"Would fix {len(violations)} print() statements")
        print_warning("Run with --fix-logging to apply changes")
        return len(violations)
    
    # Group by file
    files_to_fix: dict[Path, list[tuple[int, str]]] = {}
    for file_path, line_num, line in violations:
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append((line_num, line))
    
    # Fix each file
    for file_path, lines in files_to_fix.items():
        try:
            with file_path.open() as f:
                content = f.readlines()
            
            # Ensure logger is imported
            has_logger_import = any("import logging" in line for line in content)
            has_logger_def = any("logger = " in line for line in content)
            
            if not has_logger_import:
                # Find first import and add after it
                for i, line in enumerate(content):
                    if line.startswith("import ") or line.startswith("from "):
                        content.insert(i + 1, "import logging\n")
                        break
            
            if not has_logger_def:
                # Add logger definition after imports
                for i, line in enumerate(content):
                    if not (line.startswith("import ") or line.startswith("from ") or line.strip() == ""):
                        content.insert(i, "\nlogger = logging.getLogger(__name__)\n")
                        break
            
            # Replace print statements (simple version - may need manual review)
            new_content = []
            for line in content:
                if re.search(r"\bprint\s*\(", line) and not line.strip().startswith("#"):
                    # Simple replacement - keeps the message
                    new_line = re.sub(
                        r"print\s*\((.*?)\)",
                        r"logger.info(\1)",
                        line,
                    )
                    new_content.append(new_line)
                    fixed += 1
                else:
                    new_content.append(line)
            
            # Write back
            if not dry_run:
                with file_path.open("w") as f:
                    f.writelines(new_content)
                
                print_success(f"Fixed {len(lines)} violations in {file_path.name}")
        
        except Exception as e:  # noqa: BLE001
            print_error(f"Failed to fix {file_path}: {e}")
    
    print_success(f"\nFixed {fixed} print() statements!")
    return fixed


def find_datetime_violations() -> list[tuple[Path, int, str]]:
    """Find naive datetime.now() calls."""
    print_header("Finding datetime.now() violations")
    
    repo_root = find_repo_root()
    violations = []
    
    for py_file in repo_root.rglob("*.py"):
        if "venv" in str(py_file) or ".git" in str(py_file):
            continue
            
        try:
            with py_file.open() as f:
                for line_num, line in enumerate(f, 1):
                    # Match datetime.now() without UTC
                    if "datetime.now()" in line and "UTC" not in line and not line.strip().startswith("#"):
                        violations.append((py_file, line_num, line.strip()))
        except (UnicodeDecodeError, PermissionError):
            continue
    
    print(f"Found {len(violations)} naive datetime.now() calls\n")
    
    for file_path, line_num, line in violations:
        rel_path = file_path.relative_to(repo_root)
        print(f"  {rel_path}:{line_num}")
        print(f"    {line[:80]}")
    
    return violations


def fix_datetime_calls(dry_run: bool = True) -> int:  # noqa: FBT001, FBT002
    """Fix naive datetime.now() to datetime.now(UTC)."""
    print_header("Fixing datetime.now() calls" + (" [DRY RUN]" if dry_run else ""))
    
    violations = find_datetime_violations()
    fixed = 0
    
    if not violations:
        print_success("No violations found!")
        return 0
    
    if dry_run:
        print_warning(f"Would fix {len(violations)} datetime calls")
        print_warning("Run with --fix-datetime to apply changes")
        return len(violations)
    
    # Group by file
    files_to_fix: dict[Path, Any] = {}
    for file_path, _line_num, _line in violations:
        if file_path not in files_to_fix:
            files_to_fix[file_path] = True
    
    # Fix each file
    for file_path in files_to_fix:
        try:
            with file_path.open() as f:
                content = f.read()
            
            # Ensure UTC import
            if "from datetime import" in content and "UTC" not in content:
                content = content.replace(
                    "from datetime import",
                    "from datetime import UTC,",
                    1,
                )
            elif "import datetime" in content:
                # Add UTC import
                content = content.replace(
                    "import datetime",
                    "from datetime import UTC\nimport datetime",
                    1,
                )
            
            # Replace datetime.now() with datetime.now(UTC)
            original_count = content.count("datetime.now()")
            content = content.replace("datetime.now()", "datetime.now(UTC)")
            fixed += original_count
            
            # Write back
            if not dry_run:
                with file_path.open("w") as f:
                    f.write(content)
                
                print_success(f"Fixed datetime calls in {file_path.name}")
        
        except Exception as e:  # noqa: BLE001
            print_error(f"Failed to fix {file_path}: {e}")
    
    print_success(f"\nFixed {fixed} datetime calls!")
    return fixed


def list_todos() -> list[tuple[Path, int, str]]:
    """List all TODOs without issue links."""
    print_header("Finding TODOs without issue links")
    
    repo_root = find_repo_root()
    services_dir = repo_root / "services"
    todos = []
    
    for py_file in services_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
            
        try:
            with py_file.open() as f:
                for line_num, line in enumerate(f, 1):
                    # Match TODO without issue number
                    if "TODO" in line and "TODO(#" not in line and not line.strip().startswith("# TODO:"):
                        todos.append((py_file, line_num, line.strip()))
        except (UnicodeDecodeError, PermissionError):
            continue
    
    print(f"Found {len(todos)} TODOs without issue links\n")
    
    # Group by file
    by_file: dict[Path, list[tuple[int, str]]] = {}
    for file_path, line_num, line in todos:
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append((line_num, line))
    
    # Show grouped
    for file_path, lines in sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        rel_path = file_path.relative_to(repo_root)
        print(f"\n  {rel_path} - {len(lines)} TODOs:")
        for line_num, line in lines[:3]:
            print(f"    L{line_num}: {line[:70]}")
        if len(lines) > 3:
            print(f"    ... and {len(lines) - 3} more")
    
    print_warning("\nAction needed: Create GitHub issues and link them")
    print_warning("Example: # TODO(#123): Implement feature X")
    
    return todos


def find_duplicate_services() -> list[tuple[str, str]]:
    """Find duplicate service directories."""
    print_header("Finding duplicate service directories")
    
    repo_root = find_repo_root()
    services_dir = repo_root / "services"
    
    duplicates = [
        ("gateway-api", "gateway_api"),
        ("mao-engine", "mao-service"),
        ("marketplace", "marketplace-service"),
        ("governance", "governance-service"),
    ]
    
    found_duplicates = []
    
    for orig, dup in duplicates:
        orig_path = services_dir / orig
        dup_path = services_dir / dup
        
        if orig_path.exists() and dup_path.exists():
            found_duplicates.append((orig, dup))
            print_error(f"Found duplicate: {orig}/ and {dup}/")
    
    if not found_duplicates:
        print_success("No duplicate services found!")
    else:
        print_warning(f"\nFound {len(found_duplicates)} duplicate service pairs")
        print_warning("Manual review required to merge/delete")
    
    return found_duplicates


def main() -> None:
    """Run the remediation script."""
    parser = argparse.ArgumentParser(description="Fix VIBE coding rules violations")
    parser.add_argument("--check", action="store_true", help="Check for violations (dry run)")
    parser.add_argument("--fix-logging", action="store_true", help="Fix print() statements")
    parser.add_argument("--fix-datetime", action="store_true", help="Fix naive datetime calls")
    parser.add_argument("--list-todos", action="store_true", help="List TODOs without issues")
    parser.add_argument("--find-duplicates", action="store_true", help="Find duplicate services")
    parser.add_argument("--all", action="store_true", help="Run all checks and fixes")
    
    args = parser.parse_args()
    
    if args.all or args.check:
        find_print_violations(dry_run=True)
        find_datetime_violations()
        list_todos()
        find_duplicate_services()
    
    if args.fix_logging and not args.check:
        fix_print_statements(dry_run=False)
    
    if args.fix_datetime and not args.check:
        fix_datetime_calls(dry_run=False)
    
    if args.list_todos:
        list_todos()
    
    if args.find_duplicates:
        find_duplicate_services()
    
    if not any([args.check, args.fix_logging, args.fix_datetime, args.list_todos, args.find_duplicates, args.all]):
        parser.print_help()


if __name__ == "__main__":
    main()
