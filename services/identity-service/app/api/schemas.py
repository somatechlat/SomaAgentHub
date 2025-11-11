"""Schemas for identity service."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from services.common.config.base_settings import resolve_env


class UserRecord(BaseModel):
user_id: str
name: str
email: str
capabilities: list[str] = Field(default_factory=list)
active: bool = True
mfa_secret: str | None = None
mfa_enabled: bool = False


class TrainingLockRequest(BaseModel):
tenant_id: str
requested_by: str


class TrainingLockStatus(BaseModel):
tenant_id: str
locked: bool
locked_by: str | None = None
locked_at: datetime | None = None


class MFAEnrollResponse(BaseModel):
user_id: str
secret: str


class MFAVerifyRequest(BaseModel):
user_id: str
code: str


class TokenIssueRequest(BaseModel):
user_id: str
tenant_id: str
capabilities: list[str] = Field(default_factory=list)
mfa_code: str | None = None


class TokenResponse(BaseModel):
token: str
expires_in: int
token_type: str = "bearer"


class TokenVerifyRequest(BaseModel):
token: str
required_capabilities: list[str] = Field(default_factory=list)


class TokenVerifyResponse(BaseModel):
valid: bool
user_id: str
tenant_id: str
capabilities: list[str]
issued_at: datetime
expires_at: datetime
jti: str


class TokenRevokeRequest(BaseModel):
token: str
