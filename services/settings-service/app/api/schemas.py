"""Pydantic schemas for settings service."""

from __future__ import annotations

from typing import Dict, List, Optional

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
