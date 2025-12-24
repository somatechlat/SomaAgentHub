"""Canonical Django ORM models for SomaAgentHub control-plane."""

from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "tenant"
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - repr only
        return self.name


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="roles")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "role"
        unique_together = ("tenant", "name")
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - repr only
        return f"{self.tenant.slug}:{self.name}"


class Principal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="principals")
    email = models.EmailField()
    display_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    capabilities = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    roles = models.ManyToManyField(Role, related_name="principals", blank=True)

    class Meta:
        db_table = "principal"
        unique_together = ("tenant", "email")
        ordering = ["email"]

    def __str__(self) -> str:  # pragma: no cover - repr only
        return self.email


class Agent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="agents")
    name = models.CharField(max_length=255)
    spec = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent"
        unique_together = ("tenant", "name")
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - repr only
        return self.name


class WorkflowInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="workflow_instances")
    workflow_id = models.CharField(max_length=255)
    status = models.CharField(max_length=64, db_index=True)
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workflow_instance"
        indexes = [
            models.Index(fields=["tenant", "workflow_id"]),
            models.Index(fields=["status", "created_at"]),
        ]


class OutboxEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="outbox_events")
    event_type = models.CharField(max_length=255, db_index=True)
    payload = models.JSONField()
    status = models.CharField(max_length=32, default="pending", db_index=True)
    publish_attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "outbox_event"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["tenant", "event_type"]),
        ]


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="audit_logs")
    principal = models.ForeignKey(
        Principal, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=255, db_index=True)
    resource = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "audit_log"
        indexes = [
            models.Index(fields=["tenant", "action", "created_at"]),
        ]
