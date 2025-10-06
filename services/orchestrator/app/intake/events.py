"""Event emission helpers for the intake lifecycle."""

from __future__ import annotations

from typing import Any, Dict


class IntakeEventEmitter:
    """Abstraction around Kafka or other event sinks."""

    async def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit an intake event for auditing/analytics."""

        raise NotImplementedError("IntakeEventEmitter.emit requires integration with the event bus")
