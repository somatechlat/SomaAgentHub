"""Pydantic models representing the SomaGent constitution bundle."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env


class Principle(BaseModel):
    id: str
    title: str
    body: str


class GovernanceTopic(BaseModel):
    topic: str
    requirements: list[str]


class AuditStorage(BaseModel):
    type: str
    region: str
    bucket: str


class AuditStreams(BaseModel):
    topics: list[str]
    retention_days: int = Field(gt=0)
    storage: AuditStorage


class Enforcement(BaseModel):
    governance_topics: list[GovernanceTopic]
    audit_streams: AuditStreams


class RevisionEntry(BaseModel):
    version: str
    changes: list[str]


class Localization(BaseModel):
    default_locale: str
    available_locales: list[str]
    status: str


class ConstitutionDocument(BaseModel):
    title: str
    preamble: str
    principles: list[Principle]
    enforcement: Enforcement
    revision_history: list[RevisionEntry]
    localization: Localization


class SignatureModel(BaseModel):
    algorithm: str
    value: str


class ConstitutionBundle(BaseModel):
    version: str
    issued_at: datetime
    document: ConstitutionDocument
    hash: str
    signature: SignatureModel


class ConstitutionSummary(BaseModel):
    version: str
    issued_at: datetime
    hash: str


class HashResponse(BaseModel):
    hash: str
    version: str
    tenant: str


class ValidationResult(BaseModel):
    valid: bool
    issues: list[str] = Field(default_factory=list)
