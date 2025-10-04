"""Pydantic schemas for settings service (Marketplace removed)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TenantSettings(BaseModel):
    tenant_id: str
    display_name: str
    deployment_mode: str = "developer-light"
    budgets_tokens: int = 5000
    default_model_profile: str = "default"


class TenantSummary(BaseModel):
    tenant_id: str
    display_name: str
    deployment_mode: str


class ModelProfile(BaseModel):
    name: str = "default"
    chat: str = "stub"
    planning: str = "stub"
    code: str = "stub"
    embedding: str = "stub"
    speech_recognition: str = "whisper-large-v3"
    speech_synthesis: str = "elevenlabs-conversational-v2"


class NotificationChannel(BaseModel):
    channel: str
    enabled: bool = True
    severity_threshold: str = "info"


class NotificationPreferences(BaseModel):
    tenant_id: str
    user_id: Optional[str] = None
    quiet_hours: Optional[str] = None
    channels: List[NotificationChannel] = Field(default_factory=list)


class AttestationRecord(BaseModel):
    signer: str
    signature: str
    statement: str
    issued_at: datetime


class ComplianceIssue(BaseModel):
    code: str
    severity: str
    message: str


class ComplianceReport(BaseModel):
    passed: bool
    issues: List[ComplianceIssue] = Field(default_factory=list)


class BillingRecordRequest(BaseModel):
    tenant_id: str
    capsule_id: Optional[str] = None
    tokens: int
    cost_usd: float
    recorded_by: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BillingEvent(BaseModel):
    event_id: str
    tenant_id: str
    capsule_id: Optional[str] = None
    tokens: int
    cost_usd: float
    recorded_at: datetime
    recorded_by: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BillingLedger(BaseModel):
    tenant_id: str
    total_tokens: int
    total_cost_usd: float
    events: List[BillingEvent] = Field(default_factory=list)
