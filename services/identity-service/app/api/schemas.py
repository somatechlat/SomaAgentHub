"""Schemas for identity service."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserRecord(BaseModel):
    user_id: str
    name: str
    email: str
    capabilities: List[str] = Field(default_factory=list)
    active: bool = True
    mfa_secret: Optional[str] = None
    mfa_enabled: bool = False


class TrainingLockRequest(BaseModel):
    tenant_id: str
    requested_by: str


class TrainingLockStatus(BaseModel):
    tenant_id: str
    locked: bool
    locked_by: Optional[str] = None
    locked_at: Optional[datetime] = None


class MFAEnrollResponse(BaseModel):
    user_id: str
    secret: str


class MFAVerifyRequest(BaseModel):
    user_id: str
    code: str


class TokenIssueRequest(BaseModel):
    user_id: str
    tenant_id: str
    capabilities: List[str] = Field(default_factory=list)
    mfa_code: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    expires_in: int
