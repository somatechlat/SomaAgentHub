# Make the top‑level ``slm`` package act as a proxy for the real implementation
# located under ``services/slm-service/slm``. By extending ``__path__`` we allow
# imports like ``from slm.producer import Producer`` to resolve to the files in
# that directory without duplicating code.

import pathlib
import asyncio

_service_path = (
    pathlib.Path(__file__).resolve().parent.parent
    / "services"
    / "slm-service"
    / "slm"
)

if _service_path.is_dir():
    # Prepend so our proxy takes precedence.
    __path__.insert(0, str(_service_path))

# Ensure an event loop exists for test code that uses ``asyncio.get_event_loop``
# which raises RuntimeError when no loop is set (Python 3.11+).
class _TestLoopPolicy(asyncio.DefaultEventLoopPolicy):
    """Policy that creates a fresh loop when ``get_event_loop`` is called without one.

    This mirrors the historic ``asyncio.get_event_loop`` behaviour used by the
    existing test suite, avoiding ``RuntimeError: There is no current event loop``.
    """

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        try:
            return super().get_event_loop()
        except RuntimeError:
            # No loop set – create and install a new one.
            loop = self.new_event_loop()
            self.set_event_loop(loop)
            return loop

asyncio.set_event_loop_policy(_TestLoopPolicy())

# For environments where a loop may already exist (e.g., real server start‑up),
# we still ensure one is available.
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
