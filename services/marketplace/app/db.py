"""Marketplace database models and session management."""

from __future__ import annotations

import uuid
import json
from datetime import datetime
from typing import Generator, List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.types import TypeDecorator

# Use in-memory SQLite for testing
DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class JSONEncodedList(TypeDecorator):
    """Store a list as JSON in the database (for SQLite compatibility)."""
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return '[]'
        return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return json.loads(value)


class Capsule(Base):
    """Task capsule marketplace listing."""
    
    __tablename__ = "capsules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    author = Column(String, nullable=False)
    category = Column(String, nullable=False)
    tags = Column(JSONEncodedList, default=list)
    readme = Column(Text, nullable=True)
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    versions = relationship("CapsuleVersion", back_populates="capsule", cascade="all, delete-orphan")
    ratings = relationship("CapsuleRating", back_populates="capsule", cascade="all, delete-orphan")
    downloads = relationship("CapsuleDownload", back_populates="capsule", cascade="all, delete-orphan")


class CapsuleVersion(Base):
    """Version history for capsules."""
    
    __tablename__ = "capsule_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    capsule_id = Column(String, ForeignKey("capsules.id"), nullable=False)
    version = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    capsule = relationship("Capsule", back_populates="versions")


class CapsuleRating(Base):
    """User ratings for capsules."""
    
    __tablename__ = "capsule_ratings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    capsule_id = Column(String, ForeignKey("capsules.id"), nullable=False)
    user_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    review = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    capsule = relationship("Capsule", back_populates="ratings")


class CapsuleDownload(Base):
    """Download tracking for capsules."""
    
    __tablename__ = "capsule_downloads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    capsule_id = Column(String, ForeignKey("capsules.id"), nullable=False)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    capsule = relationship("Capsule", back_populates="downloads")


# Create tables
Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for dependency injection.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
