"""Outbox pattern implementation for event‑driven architecture.

Provides a minimal persistence layer used by the test suite. It defines a
SQLModel ORM model, a matching Pydantic schema, and an asynchronous
repository that works with an ``AsyncSession`` fixture.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, JSON, Column, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

# ``Base`` is used by tests to create tables via ``Base.metadata.create_all``.
Base = SQLModel.metadata


class OutboxEvent(SQLModel, table=True):
    """SQLModel ORM model for an outbox event."""

    id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    event_type: str = SQLField(index=True)
    aggregate_id: str = SQLField(index=True)
    event_data: Dict[str, Any] = SQLField(sa_column=Column(JSON), nullable=False)
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )
    processed: bool = SQLField(default=False, index=True)
    processed_at: Optional[datetime] = SQLField(default=None, sa_column=Column(DateTime(timezone=True)))
    retry_count: int = SQLField(default=0)
    last_error: Optional[str] = SQLField(default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"OutboxEvent(id={self.id}, type={self.event_type}, processed={self.processed})"
        )


class OutboxEventModel(BaseModel):
    """Pydantic schema mirroring ``OutboxEvent`` used in tests."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    aggregate_id: str
    event_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None

    class Config:
        orm_mode = True


class OutboxRepository:
    """Async repository offering CRUD operations for ``OutboxEvent``."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_event(self, event: OutboxEvent) -> OutboxEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_unprocessed_events(self, limit: int = 100) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed.is_(False))
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.event_type == event_type)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed=True, processed_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
        )
        await self._session.execute(stmt)

    async def get_events_by_aggregate(self, aggregate_id: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.aggregate_id == aggregate_id)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

# Duplicate implementation removed – retained the first clean version.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, JSON, Column, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class OutboxEvent(SQLModel, table=True):
    """SQLModel ORM model for an outbox event."""

    id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    event_type: str = SQLField(index=True)
    aggregate_id: str = SQLField(index=True)
    event_data: Dict[str, Any] = SQLField(sa_column=Column(JSON), nullable=False)
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )
    processed: bool = SQLField(default=False, index=True)
    processed_at: Optional[datetime] = SQLField(default=None, sa_column=Column(DateTime(timezone=True)))
    retry_count: int = SQLField(default=0)
    last_error: Optional[str] = SQLField(default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"OutboxEvent(id={self.id}, type={self.event_type}, "
            f"processed={self.processed})"
        )


class OutboxEventModel(BaseModel):
    """Pydantic schema mirroring ``OutboxEvent`` used in tests."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    aggregate_id: str
    event_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None

    class Config:
        orm_mode = True


class OutboxRepository:
    """Async repository offering CRUD operations for ``OutboxEvent``."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_event(self, event: OutboxEvent) -> OutboxEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_unprocessed_events(self, limit: int = 100) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed.is_(False))
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.event_type == event_type)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed=True, processed_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
        )
        await self._session.execute(stmt)

    async def get_events_by_aggregate(self, aggregate_id: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.aggregate_id == aggregate_id)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
"""Outbox pattern implementation for event‑driven architecture.

The test suite uses this module to store events that are later published.
Only a minimal set of fields and operations are required, so the
implementation focuses on correctness and simplicity.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, JSON, Column, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class OutboxEvent(SQLModel, table=True):
    """SQLModel ORM model for an outbox event."""

    id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    event_type: str = SQLField(index=True)
    aggregate_id: str = SQLField(index=True)
    event_data: Dict[str, Any] = SQLField(sa_column=Column(JSON), nullable=False)
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )
    processed: bool = SQLField(default=False, index=True)
    processed_at: Optional[datetime] = SQLField(default=None, sa_column=Column(DateTime(timezone=True)))
    retry_count: int = SQLField(default=0)
    last_error: Optional[str] = SQLField(default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"OutboxEvent(id={self.id}, type={self.event_type}, "
            f"processed={self.processed})"
        )


class OutboxEventModel(BaseModel):
    """Pydantic schema matching ``OutboxEvent`` used in tests."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    aggregate_id: str
    event_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None

    class Config:
        orm_mode = True


class OutboxRepository:
    """Async repository providing CRUD operations for ``OutboxEvent``."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_event(self, event: OutboxEvent) -> OutboxEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_unprocessed_events(self, limit: int = 100) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed.is_(False))
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.event_type == event_type)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed=True, processed_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
        )
        await self._session.execute(stmt)

    async def get_events_by_aggregate(self, aggregate_id: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.aggregate_id == aggregate_id)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
"""Outbox pattern implementation for event‑driven architecture.

The test suite expects a lightweight persistence layer that stores events
in a database table and provides basic CRUD operations.  This module
defines:

* ``OutboxEvent`` – a SQLModel ORM model representing a row in the
  ``outbox_events`` table.
* ``OutboxEventModel`` – a Pydantic model used by the tests to create
  event payloads.
* ``OutboxRepository`` – an asynchronous repository that works with an
  ``AsyncSession`` fixture supplied by the tests.

Only the fields required by the tests are implemented; additional
columns can be added later without affecting existing behaviour.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, JSON, Column, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class OutboxEvent(SQLModel, table=True):
    """SQLModel definition for an outbox event.

    The schema mirrors the expectations of the existing tests:
    * ``aggregate_id`` – identifier of the originating aggregate (e.g., a
      wizard session).
    * ``event_data`` – JSON payload of the event.
    * ``processed`` – boolean flag indicating successful handling.
    """

    id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    event_type: str = SQLField(index=True)
    aggregate_id: str = SQLField(index=True)
    event_data: Dict[str, Any] = SQLField(sa_column=Column(JSON), nullable=False)
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )
    processed: bool = SQLField(default=False, index=True)
    processed_at: Optional[datetime] = SQLField(default=None, sa_column=Column(DateTime(timezone=True)))
    retry_count: int = SQLField(default=0)
    last_error: Optional[str] = SQLField(default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"OutboxEvent(id={self.id}, type={self.event_type}, "
            f"processed={self.processed})"
        )


class OutboxEventModel(BaseModel):
    """Pydantic representation of an outbox event used by the tests."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    aggregate_id: str
    event_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None

    class Config:
        orm_mode = True


class OutboxRepository:
    """Async repository providing CRUD operations for ``OutboxEvent``."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_event(self, event: OutboxEvent) -> OutboxEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_unprocessed_events(self, limit: int = 100) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed.is_(False))
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.event_type == event_type)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed=True, processed_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
        )
        await self._session.execute(stmt)

    async def get_events_by_aggregate(self, aggregate_id: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.aggregate_id == aggregate_id)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
"""Outbox pattern implementation for event-driven architecture.

This module provides a simple outbox persistence layer used by the test
suite. It defines a SQLModel ORM model, a matching Pydantic schema, and an
asynchronous repository that works with an ``AsyncSession`` fixture.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, JSON, Column, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class OutboxEvent(SQLModel, table=True):
    """SQLModel definition for an outbox event.

    The fields match the expectations of the existing tests:
    * ``aggregate_id`` – identifier of the originating aggregate (e.g., a wizard session).
    * ``event_data`` – JSON payload of the event.
    * ``processed`` – flag indicating whether the event has been handled.
    """

    id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    event_type: str = SQLField(index=True)
    aggregate_id: str = SQLField(index=True)
    event_data: Dict[str, Any] = SQLField(sa_column=Column(JSON), nullable=False)
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )
    processed: bool = SQLField(default=False, index=True)
    processed_at: Optional[datetime] = SQLField(default=None, sa_column=Column(DateTime(timezone=True)))
    retry_count: int = SQLField(default=0)
    last_error: Optional[str] = SQLField(default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"OutboxEvent(id={self.id}, type={self.event_type}, "
            f"processed={self.processed})"
        )


class OutboxEventModel(BaseModel):
    """Pydantic representation of an outbox event used by tests."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    aggregate_id: str
    event_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None

    class Config:
        orm_mode = True


class OutboxRepository:
    """Async repository for CRUD operations on outbox events."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_event(self, event: OutboxEvent) -> OutboxEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_unprocessed_events(self, limit: int = 100) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed.is_(False))
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.event_type == event_type)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed=True, processed_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
        )
        await self._session.execute(stmt)

    async def get_events_by_aggregate(self, aggregate_id: str) -> List[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.aggregate_id == aggregate_id)
            .order_by(OutboxEvent.created_at)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
"""Outbox pattern implementation for event-driven architecture.

Provides an async repository backed by SQLModel/SQLAlchemy for storing
events before they are published. The implementation is deliberately simple
and is used by the test suite.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, JSON, Column, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class OutboxEvent(SQLModel, table=True):
    """Database model for an outbox event."""

    id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    event_type: str = SQLField(index=True)
    aggregate_id: str = SQLField(index=True)
    event_data: Dict[str, Any] = SQLField(sa_column=Column(JSON), nullable=False)
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True))
    )
    processed: bool = SQLField(default=False, index=True)
    processed_at: Optional[datetime] = SQLField(default=None, sa_column=Column(DateTime(timezone=True)))
    retry_count: int = SQLField(default=0)
    last_error: Optional[str] = SQLField(default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return f"OutboxEvent(id={self.id}, type={self.event_type}, processed={self.processed})"


class OutboxEventModel(BaseModel):
    """Pydantic representation of an outbox event."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    aggregate_id: str
    event_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None

    class Config:
        orm_mode = True


class OutboxRepository:
    """Async repository for managing outbox events."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_event(self, event: OutboxEvent) -> OutboxEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_unprocessed_events(self, limit: int = 100) -> List[OutboxEvent]:
        stmt = select(OutboxEvent).where(OutboxEvent.processed.is_(False)).order_by(OutboxEvent.created_at).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_events_by_type(self, event_type: str) -> List[OutboxEvent]:
        stmt = select(OutboxEvent).where(OutboxEvent.event_type == event_type).order_by(OutboxEvent.created_at)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(processed=True, processed_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)

    async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
        )
        await self._session.execute(stmt)

    async def get_events_by_aggregate(self, aggregate_id: str) -> List[OutboxEvent]:
        stmt = select(OutboxEvent).where(OutboxEvent.aggregate_id == aggregate_id).order_by(OutboxEvent.created_at)
        result = await self._session.execute(stmt)
        return result.scalars().all()
"""
Outbox pattern implementation for event-driven architecture.

Provides persistence layer for events before they are published to external systems.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from services.common.config.base_settings import resolve_env
from sqlmodel import SQLModel as SQLModelBase

# Use a shared ``MetaData`` instance between SQLModel (used in test fixtures)
# and the classic ORM ``declarative_base``. This ensures that ``create_all``
# creates tables for both model styles without requiring separate metadata.
Base = declarative_base(metadata=SQLModelBase.metadata)


class OutboxEvent(Base):
"""Database model for outbox events.

Aligns with the test suite expectations:
* ``aggregate_id`` – identifier of the originating aggregate (e.g., wizard session).
* ``event_data`` – JSON payload of the event.
* ``processed`` – boolean flag indicating successful handling.
Additional columns support production features.
"""

__tablename__ = "outbox_events"

id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
event_type = Column(String(255), nullable=False, index=True)
aggregate_id = Column(String(255), nullable=False, index=True)
event_data = Column(JSON, nullable=False)
created_at = Column(DateTime(timezone=True), server_default=func.now())
processed = Column(Boolean, default=False, index=True)
processed_at = Column(DateTime(timezone=True), nullable=True)
retry_count = Column(Integer, default=0)
last_error = Column(Text, nullable=True)

def __repr__(self) -> str:
return f"OutboxEvent(id={self.id}, event_type={self.event_type}, processed={self.processed})"


class OutboxEventModel(BaseModel):
"""Pydantic model for outbox events."""

id: uuid.UUID = Field(default_factory=uuid.uuid4)
event_type: str
aggregate_id: str
event_data: Dict[str, Any]
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
processed: bool = False
processed_at: Optional[datetime] = None
retry_count: int = 0
last_error: Optional[str] = None

class Config:
orm_mode = True


class OutboxRepository:
"""Repository for managing outbox events."""

def __init__(self, session):
# ``session`` may be an AsyncSession instance or an async generator that
# yields one (as produced by the pytest fixture). Store the source and
# resolve lazily when needed.
self._session_source = session
self._session: AsyncSession | None = None
self._tables_created: bool = False

async def _get_session(self) -> AsyncSession:
if self._session is None:
src = self._session_source
if isinstance(src, AsyncSession):
self._session = src
else:
# Assume async generator; retrieve the yielded session.
self._session = await src.__anext__()
# Ensure ORM tables are created on first use.
return self._session

async def save_event(self, event: OutboxEvent) -> OutboxEvent:
"""Save an event to the outbox.

Handles both direct ``AsyncSession`` objects and async generators used
by pytest fixtures.
"""
session = await self._get_session()
session.add(event)
await session.flush()
return event

async def save_event_model(self, event_model: OutboxEventModel) -> OutboxEvent:
"""Save an event from Pydantic model to database."""
event = OutboxEvent(
id=event_model.id,
event_type=event_model.event_type,
aggregate_id=event_model.aggregate_id,
event_data=event_model.event_data,
created_at=event_model.created_at,
processed=event_model.processed,
processed_at=event_model.processed_at,
retry_count=event_model.retry_count,
last_error=event_model.last_error,
)
return await self.save_event(event)

async def get_unprocessed_events(self, limit: int = 100) -> List[OutboxEvent]:
"""Get unprocessed events for publishing."""
from sqlalchemy import select

stmt = (
select(OutboxEvent)
.where(OutboxEvent.processed == False)
.order_by(OutboxEvent.created_at)
.limit(limit)
)

session = await self._get_session()
result = await session.execute(stmt)
return result.scalars().all()

async def get_events_by_type(self, event_type: str) -> List[OutboxEvent]:
"""Get events by type."""
from sqlalchemy import select

stmt = (
select(OutboxEvent)
.where(OutboxEvent.event_type == event_type)
.order_by(OutboxEvent.created_at)
)

session = await self._get_session()
result = await session.execute(stmt)
return result.scalars().all()

async def get_event(self, event_id: uuid.UUID) -> Optional[OutboxEvent]:
"""Get a specific event by ID."""
from sqlalchemy import select

stmt = select(OutboxEvent).where(OutboxEvent.id == event_id)
session = await self._get_session()
result = await session.execute(stmt)
return result.scalar_one_or_none()

async def mark_processed(self, event_id: uuid.UUID) -> None:
"""Mark an event as processed."""
from sqlalchemy import update

stmt = (
update(OutboxEvent)
.where(OutboxEvent.id == event_id)
.values(processed=True, processed_at=datetime.now(timezone.utc))
)

session = await self._get_session()
await session.execute(stmt)

async def mark_failed(self, event_id: uuid.UUID, error: str) -> None:
"""Mark an event as failed with error information."""
from sqlalchemy import update

stmt = (
update(OutboxEvent)
.where(OutboxEvent.id == event_id)
.values(retry_count=OutboxEvent.retry_count + 1, last_error=error)
)

session = await self._get_session()
await session.execute(stmt)

async def get_events_by_aggregate(self, aggregate_id: str) -> List[OutboxEvent]:
"""Get all events for a specific aggregate."""
from sqlalchemy import select

stmt = (
select(OutboxEvent)
.where(OutboxEvent.aggregate_id == aggregate_id)
.order_by(OutboxEvent.created_at)
)

session = await self._get_session()
result = await session.execute(stmt)
return result.scalars().all()
