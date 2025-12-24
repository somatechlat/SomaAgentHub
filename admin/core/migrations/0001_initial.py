# Generated migration for admin.core initial models
from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=255, unique=True)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("created_at", models.DateTimeField(default=timezone.now, db_index=True)),
            ],
            options={
                "db_table": "tenant",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=timezone.now, db_index=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="roles", to="admin.core.tenant"
                    ),
                ),
            ],
            options={
                "db_table": "role",
                "ordering": ["name"],
                "unique_together": {("tenant", "name")},
            },
        ),
        migrations.CreateModel(
            name="Principal",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("email", models.EmailField(max_length=254)),
                ("display_name", models.CharField(max_length=255, blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("capabilities", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(default=timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="principals", to="admin.core.tenant"
                    ),
                ),
            ],
            options={
                "db_table": "principal",
                "ordering": ["email"],
                "unique_together": {("tenant", "email")},
            },
        ),
        migrations.CreateModel(
            name="Agent",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("spec", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(default=timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="agents", to="admin.core.tenant"
                    ),
                ),
            ],
            options={
                "db_table": "agent",
                "ordering": ["name"],
                "unique_together": {("tenant", "name")},
            },
        ),
        migrations.CreateModel(
            name="WorkflowInstance",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("workflow_id", models.CharField(max_length=255)),
                ("status", models.CharField(max_length=64, db_index=True)),
                ("result", models.JSONField(null=True, blank=True)),
                ("created_at", models.DateTimeField(default=timezone.now, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workflow_instances",
                        to="admin.core.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "workflow_instance",
            },
        ),
        migrations.CreateModel(
            name="OutboxEvent",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("event_type", models.CharField(max_length=255, db_index=True)),
                ("payload", models.JSONField()),
                ("status", models.CharField(max_length=32, default="pending", db_index=True)),
                ("publish_attempts", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(default=timezone.now, db_index=True)),
                ("published_at", models.DateTimeField(null=True, blank=True, db_index=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outbox_events",
                        to="admin.core.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "outbox_event",
            },
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("action", models.CharField(max_length=255, db_index=True)),
                ("resource", models.CharField(max_length=255)),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(default=timezone.now, db_index=True)),
                (
                    "principal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        null=True,
                        blank=True,
                        to="admin.core.principal",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audit_logs",
                        to="admin.core.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "audit_log",
            },
        ),
        migrations.AddIndex(
            model_name="workflowinstance",
            index=models.Index(fields=["tenant", "workflow_id"], name="workflow_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowinstance",
            index=models.Index(fields=["status", "created_at"], name="workflow_status_idx"),
        ),
        migrations.AddIndex(
            model_name="outboxevent",
            index=models.Index(fields=["status", "created_at"], name="outbox_status_idx"),
        ),
        migrations.AddIndex(
            model_name="outboxevent",
            index=models.Index(fields=["tenant", "event_type"], name="outbox_type_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["tenant", "action", "created_at"], name="audit_idx"),
        ),
        migrations.AddField(
            model_name="principal",
            name="roles",
            field=models.ManyToManyField(blank=True, related_name="principals", to="admin.core.role"),
        ),
    ]
