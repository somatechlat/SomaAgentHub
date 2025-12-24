#!/usr/bin/env python
"""Django entrypoint for the SomaAgentHub control-plane."""

from __future__ import annotations

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sah_django.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:  # pragma: no cover
        raise ImportError("Django is required. Install dependencies before running manage.py.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
