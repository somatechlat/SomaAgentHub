"""Django admin registrations for SomaAgentHub core models."""

from __future__ import annotations

from django.contrib import admin

from .models import Agent, AuditLog, OutboxEvent, Principal, Role, Tenant, WorkflowInstance


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    ordering = ("name",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "created_at")
    list_filter = ("tenant",)
    search_fields = ("name", "tenant__name", "tenant__slug")
    ordering = ("tenant__name", "name")


@admin.register(Principal)
class PrincipalAdmin(admin.ModelAdmin):
    list_display = ("email", "tenant", "is_active", "created_at")
    list_filter = ("tenant", "is_active")
    search_fields = ("email", "tenant__name", "tenant__slug")
    filter_horizontal = ("roles",)
    ordering = ("email",)


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "created_at")
    list_filter = ("tenant",)
    search_fields = ("name", "tenant__name", "tenant__slug")
    ordering = ("name",)


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ("workflow_id", "tenant", "status", "created_at")
    list_filter = ("tenant", "status")
    search_fields = ("workflow_id", "tenant__name", "tenant__slug")
    ordering = ("-created_at",)


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "tenant", "status", "created_at", "published_at", "publish_attempts")
    list_filter = ("tenant", "status", "event_type")
    search_fields = ("event_type", "tenant__name", "tenant__slug")
    ordering = ("-created_at",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "tenant", "principal", "created_at")
    list_filter = ("tenant", "action")
    search_fields = ("action", "resource", "principal__email", "tenant__name", "tenant__slug")
    ordering = ("-created_at",)
