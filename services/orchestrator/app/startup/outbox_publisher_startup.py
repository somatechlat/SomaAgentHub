"""
Startup configuration for the outbox publisher service.

Integrates background event publishing into the FastAPI lifecycle.
"""

import logging

from fastapi import FastAPI

from services.common.config.base_settings import resolve_env

from ..database import AsyncSessionLocal as get_session_factory
from ..services.outbox_publisher import create_outbox_publisher_service

logger = logging.getLogger(__name__)


class OutboxPublisherStartup:
    """Manages outbox publisher service lifecycle."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.publisher_service: OutboxPublisherStartup | None = None

    def setup_event_handlers(self) -> None:
        """Setup FastAPI startup/shutdown event handlers."""
        self.app.add_event_handler("startup", self.start_publisher)
        self.app.add_event_handler("shutdown", self.stop_publisher)

    async def start_publisher(self) -> None:
        """Start the outbox publisher service on startup."""
        try:
            kafka_servers = resolve_env("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            session_factory = get_session_factory()

            self.publisher_service = await create_outbox_publisher_service(
                session_factory=session_factory,
                kafka_bootstrap_servers=kafka_servers,
            )

            await self.publisher_service.start()
            logger.info(
                f"Outbox publisher service started successfully (bootstrap={kafka_servers})"
            )

        except Exception as e:
            logger.error(f"Failed to start outbox publisher service: {e}")
            # Don't prevent app startup, but log the error

    async def stop_publisher(self) -> None:
        """Stop the outbox publisher service on shutdown."""
        if self.publisher_service:
            try:
                await self.publisher_service.stop()
                logger.info("Outbox publisher service stopped successfully")
            except Exception as e:
                logger.error(f"Failed to stop outbox publisher service: {e}")


def setup_outbox_publisher(app: FastAPI) -> None:
    """Configure outbox publisher service for the FastAPI app."""
    startup = OutboxPublisherStartup(app)
    startup.setup_event_handlers()
