"""Top-level shim for app.core.bus.

Re-exports the notification bus implementation from the notification-service.
Tests that import ``from app.core.bus import get_notification_bus`` will
receive the concrete implementation from ``services.notification-service.app.core.bus``.
"""

from __future__ import annotations

try:
    # Import from the notification-service
    from services.notification_service.app.core.bus import (
        NotificationBus,
        get_notification_bus,
    )
    
    __all__ = ["NotificationBus", "get_notification_bus"]
except ImportError:
    # Fallback if notification-service is not available
    import warnings
    warnings.warn(
        "notification-service not available; app.core.bus functionality limited",
        ImportWarning,
    )
    
    # Provide stub implementations
    class NotificationBus:  # type: ignore
        """Stub NotificationBus when service is unavailable."""
        pass
    
    def get_notification_bus(*args, **kwargs):  # type: ignore
        """Stub get_notification_bus when service is unavailable."""
        raise ImportError("notification-service not available")
    
    __all__ = ["NotificationBus", "get_notification_bus"]
