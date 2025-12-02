"""Event emission helpers for the intake lifecycle."""

from __future__ import annotations

from typing import Any

from services.common.config.base_settings import resolve_env
from services.common.events.publisher import EventPublisher


class IntakeEventEmitter:
    """Abstraction around the central event‑bus.

    The original implementation raised ``NotImplementedError`` because the
    project did not yet have a unified event publisher.  We now have a
    concrete ``EventPublisher`` class in ``services.common.events.publisher``
    that wraps the shared ``KafkaClient``.  This method therefore publishes an
    intake‑type audit event using that wrapper.
    """

    async def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        """Emit an intake event for auditing/analytics.

        Parameters
        ----------
        event_type: str
        A short identifier for the type of intake event (e.g. ``"file.upload"``).
        payload: dict[str, Any]
        Arbitrary JSON‑serialisable data describing the event.
        """

        # Resolve optional environment variables that may be needed for the
        # audit payload.  ``resolve_env`` is a lightweight wrapper that falls
        # back to ``None`` when the variable is missing – this matches the
        # historic behaviour of the service.
        tenant_id = resolve_env("TENANT_ID", "unknown")
        user_id = resolve_env("USER_ID", "system")
        session_id = resolve_env("SESSION_ID", "none")

        # Use the central ``EventPublisher`` to send the audit event.  The
        # publisher automatically adds an ``event_id`` and timestamps.
        await EventPublisher.publish_audit(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            payload=payload,
        )
