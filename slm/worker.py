"""Compatibility wrapper for the slm-service worker.

The original worker implementation lives in
`services/slm-service/slm/worker.py`. Importing that module directly
is problematic because the directory name contains a hyphen, which
cannot be used in a Python import statement. This wrapper loads the
real module from its file path using ``importlib`` and re‑exports the
public callables expected by the test suite.
"""
import importlib.util
import os

# Resolve the absolute path to the actual worker implementation.
_current_dir = os.path.abspath(os.path.dirname(__file__))
# The worker implementation lives in the sibling 'services' directory.
_module_path = os.path.abspath(
    os.path.join(
        _current_dir,
        "..",
        "services",
        "slm-service",
        "slm",
        "worker.py",
    )
)

spec = importlib.util.spec_from_file_location("slm_service_worker", _module_path)
_slm_worker = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Unable to load slm worker module"
spec.loader.exec_module(_slm_worker)

# Re‑export the key functions so that `from slm.worker import …` works.
process_request_message = _slm_worker.process_request_message
consume_and_process = _slm_worker.consume_and_process
run_worker = _slm_worker.run_worker
start_worker = _slm_worker.start_worker

__all__ = [
    "process_request_message",
    "consume_and_process",
    "run_worker",
    "start_worker",
]
