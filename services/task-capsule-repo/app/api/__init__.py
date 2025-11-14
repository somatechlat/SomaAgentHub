"""API package for the Task Capsule Repository service.

The package exposes a FastAPI ``APIRouter`` that is imported by ``main.py``.
All route definitions live in ``routes.py``.
"""

from .routes import router  # noqa: F401