"""Pydantic models representing the SomaGent constitution bundle."""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class Principle(BaseModel):
    id: str
    title: str
    body: str


class GovernanceTopic(BaseModel):
    topic: str
    requirements: List[str]


class AuditStorage(BaseModel):
    type: str
    region: str
    bucket: str


class AuditStreams(BaseModel):
    topics: List[str]
    retention_days: int = Field(gt=0)
    storage: AuditStorage


class Enforcement(BaseModel):
    governance_topics: List[GovernanceTopic]
    audit_streams: AuditStreams


class RevisionEntry(BaseModel):
    version: str
    changes: List[str]


class Localization(BaseModel):
    default_locale: str
    available_locales: List[str]
    status: str


class ConstitutionDocument(BaseModel):
    title: str
    preamble: str
    principles: List[Principle]
    enforcement: Enforcement
    revision_history: List[RevisionEntry]
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
    issues: List[str] = Field(default_factory=list)
