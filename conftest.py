import asyncio
import httpx
from httpx import AsyncClient as OriginalAsyncClient, ASGITransport

# Patch httpx.AsyncClient to accept `app` and `base_url` for ASGI testing.
class PatchedAsyncClient(OriginalAsyncClient):
    def __init__(self, *args, app=None, base_url=None, **kwargs):
        if app is not None:
            # ASGITransport does not accept a ``base_url`` argument; the base URL
            # is provided to the AsyncClient itself. Create the transport with
            # only the app and let ``base_url`` be handled by the parent class.
            transport = ASGITransport(app=app)
            kwargs.setdefault("transport", transport)
        # Pass the base_url to the original AsyncClient if supplied.
        if base_url is not None:
            kwargs.setdefault("base_url", base_url)
        super().__init__(*args, **kwargs)

# Apply the patch globally.
httpx.AsyncClient = PatchedAsyncClient

# Provide a simple helper to run async callables synchronously, matching the
# custom usage in the test suite: ``pytest.run(asyncio=True)(func)(...)``.
def _run(**kwargs):  # noqa: D401
    """Return a wrapper that optionally runs a coroutine synchronously.

    The original tests call ``pytest.run(asyncio=True)(func)(…)``. We accept any
    keyword arguments and look for ``asyncio`` to decide whether to execute the
    function in the event loop.
    """

    asyncio_flag = kwargs.get("asyncio", False)

    def wrapper(func):
        def inner(*args, **inner_kwargs):
            if asyncio_flag:
                return asyncio.get_event_loop().run_until_complete(func(*args, **inner_kwargs))
            return func(*args, **inner_kwargs)
        return inner
    return wrapper

# Attach the helper to the pytest module so that ``pytest.run`` works.
import pytest
pytest.run = _run
