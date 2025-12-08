"""
Capsule Service - Business logic for Capsule management

Handles Capsule lifecycle, instance resolution, and OPA policy validation.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import and_, select

from services.common.models.capsule_complete import (
    CapsuleDefinition,
    CapsuleDefinitionCreate,
    CapsuleDefinitionResponse,
    CapsuleInstance,
    CapsuleInstanceCreate,
    CapsuleInstanceResponse,
    CapsuleScope,
    CapsuleStatus,
)
from services.orchestrator.app.database import get_async_session


class CapsuleService:
    """Service for managing Capsules and their instances"""

    async def create_definition(
        self, capsule_data: CapsuleDefinitionCreate
    ) -> CapsuleDefinitionResponse:
        """
        Create a new Capsule definition.

        Args:
            capsule_data: Capsule definition data

        Returns:
            Created Capsule definition

        Raises:
            ValueError: If validation fails or name+version exists
        """
        async with get_async_session() as session:
            # Check for name+version uniqueness within tenant
            stmt = select(CapsuleDefinition).where(
                and_(
                    CapsuleDefinition.tenant_id == capsule_data.tenant_id,
                    CapsuleDefinition.name == capsule_data.name,
                    CapsuleDefinition.version == capsule_data.version,
                )
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                raise ValueError(
                    f"Capsule '{capsule_data.name}' version {capsule_data.version} "
                    f"already exists for this tenant"
                )

            # Validate tool lists don't overlap
            allowed_set = set(capsule_data.allowed_tools)
            prohibited_set = set(capsule_data.prohibited_tools)
            overlap = allowed_set & prohibited_set

            if overlap:
                raise ValueError(
                    f"Tools cannot be in both allowed and prohibited lists: {overlap}"
                )

            # Create Capsule definition
            capsule = CapsuleDefinition(
                tenant_id=capsule_data.tenant_id,
                name=capsule_data.name,
                version=capsule_data.version,
                description=capsule_data.description,
                status=CapsuleStatus.DRAFT,
                # Persona
                default_persona_ref_id=capsule_data.default_persona_ref_id,
                role_overrides=capsule_data.role_overrides,
                # Tools
                allowed_tools=capsule_data.allowed_tools,
                prohibited_tools=capsule_data.prohibited_tools,
                allowed_mcp_servers=capsule_data.allowed_mcp_servers,
                tool_risk_profile=capsule_data.tool_risk_profile,
                # Runtime
                max_wall_clock_seconds=capsule_data.max_wall_clock_seconds,
                max_concurrent_nodes=capsule_data.max_concurrent_nodes,
                allowed_runtimes=capsule_data.allowed_runtimes,
                resource_profile=capsule_data.resource_profile,
                # Network
                allowed_domains=capsule_data.allowed_domains,
                blocked_domains=capsule_data.blocked_domains,
                egress_mode=capsule_data.egress_mode,
                # Policy
                opa_policy_packages=capsule_data.opa_policy_packages,
                guardrail_profiles=capsule_data.guardrail_profiles,
                # HITL
                default_hitl_mode=capsule_data.default_hitl_mode,
                risk_thresholds=capsule_data.risk_thresholds,
                max_pending_hitl=capsule_data.max_pending_hitl,
                # RL
                rl_export_allowed=capsule_data.rl_export_allowed,
                rl_export_scope=capsule_data.rl_export_scope,
                rl_excluded_fields=capsule_data.rl_excluded_fields,
                example_store_policy=capsule_data.example_store_policy,
                # Compliance
                data_classification=capsule_data.data_classification,
                retention_policy_days=capsule_data.retention_policy_days,
            )

            session.add(capsule)
            await session.commit()
            await session.refresh(capsule)

            return CapsuleDefinitionResponse.from_orm(capsule)

    async def get_definition(
        self, capsule_id: UUID, tenant_id: UUID
    ) -> CapsuleDefinitionResponse | None:
        """
        Get Capsule definition by ID with tenant isolation.

        Args:
            capsule_id: Capsule UUID
            tenant_id: Tenant UUID

        Returns:
            Capsule if found, None otherwise
        """
        async with get_async_session() as session:
            stmt = select(CapsuleDefinition).where(
                and_(
                    CapsuleDefinition.id == capsule_id,
                    CapsuleDefinition.tenant_id == tenant_id,
                )
            )
            result = await session.execute(stmt)
            capsule = result.scalar_one_or_none()

            if capsule:
                return CapsuleDefinitionResponse.from_orm(capsule)
            return None

    async def list_definitions(
        self,
        tenant_id: UUID,
        status: CapsuleStatus | None = None,
        name: str | None = None,
    ) -> list[CapsuleDefinitionResponse]:
        """
        List Capsule definitions with filters.

        Args:
            tenant_id: Tenant UUID
            status: Optional status filter
            name: Optional name filter

        Returns:
            List of Capsule definitions
        """
        async with get_async_session() as session:
            stmt = select(CapsuleDefinition).where(
                CapsuleDefinition.tenant_id == tenant_id
            )

            if status:
                stmt = stmt.where(CapsuleDefinition.status == status)

            if name:
                stmt = stmt.where(CapsuleDefinition.name == name)

            stmt = stmt.order_by(
                CapsuleDefinition.name.asc(), CapsuleDefinition.version.desc()
            )

            result = await session.execute(stmt)
            capsules = result.scalars().all()

            return [CapsuleDefinitionResponse.from_orm(c) for c in capsules]

    async def activate_definition(
        self, capsule_id: UUID, tenant_id: UUID
    ) -> CapsuleDefinitionResponse | None:
        """
        Activate a Capsule definition (makes it immutable).

        Args:
            capsule_id: Capsule UUID
            tenant_id: Tenant UUID

        Returns:
            Updated Capsule if found, None otherwise

        Raises:
            ValueError: If Capsule is already ACTIVE or DEPRECATED
        """
        async with get_async_session() as session:
            stmt = select(CapsuleDefinition).where(
                and_(
                    CapsuleDefinition.id == capsule_id,
                    CapsuleDefinition.tenant_id == tenant_id,
                )
            )
            result = await session.execute(stmt)
            capsule = result.scalar_one_or_none()

            if not capsule:
                return None

            if capsule.status != CapsuleStatus.DRAFT:
                raise ValueError(
                    f"Cannot activate Capsule in {capsule.status} status. "
                    f"Only DRAFT Capsules can be activated."
                )

            capsule.status = CapsuleStatus.ACTIVE

            await session.commit()
            await session.refresh(capsule)

            return CapsuleDefinitionResponse.from_orm(capsule)

    async def create_instance(
        self, instance_data: CapsuleInstanceCreate
    ) -> CapsuleInstanceResponse:
        """
        Create a Capsule instance with resolved configuration.

        Args:
            instance_data: Capsule instance data

        Returns:
            Created Capsule instance

        Raises:
            ValueError: If definition doesn't exist or is not ACTIVE
        """
        async with get_async_session() as session:
            # Verify definition exists and is ACTIVE
            def_stmt = select(CapsuleDefinition).where(
                and_(
                    CapsuleDefinition.id == instance_data.capsule_definition_id,
                    CapsuleDefinition.tenant_id == instance_data.tenant_id,
                    CapsuleDefinition.version
                    == instance_data.capsule_definition_version,
                )
            )
            def_result = await session.execute(def_stmt)
            definition = def_result.scalar_one_or_none()

            if not definition:
                raise ValueError(
                    f"Capsule definition {instance_data.capsule_definition_id} "
                    f"version {instance_data.capsule_definition_version} not found"
                )

            if definition.status != CapsuleStatus.ACTIVE:
                raise ValueError(
                    f"Cannot create instance from Capsule in {definition.status} status. "
                    f"Only ACTIVE Capsules can be instantiated."
                )

            # Create instance
            instance = CapsuleInstance(
                tenant_id=instance_data.tenant_id,
                capsule_definition_id=instance_data.capsule_definition_id,
                capsule_definition_version=instance_data.capsule_definition_version,
                scope=instance_data.scope,
                scope_reference=instance_data.scope_reference,
                effective_config=instance_data.effective_config,
                derived_from_id=instance_data.derived_from_id,
            )

            session.add(instance)
            await session.commit()
            await session.refresh(instance)

            return CapsuleInstanceResponse.from_orm(instance)

    async def get_instance(
        self, instance_id: UUID, tenant_id: UUID
    ) -> CapsuleInstanceResponse | None:
        """
        Get Capsule instance by ID with tenant isolation.

        Args:
            instance_id: Instance UUID
            tenant_id: Tenant UUID

        Returns:
            Instance if found, None otherwise
        """
        async with get_async_session() as session:
            stmt = select(CapsuleInstance).where(
                and_(
                    CapsuleInstance.id == instance_id,
                    CapsuleInstance.tenant_id == tenant_id,
                )
            )
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if instance:
                return CapsuleInstanceResponse.from_orm(instance)
            return None

    async def resolve_instance(
        self,
        definition_id: UUID,
        tenant_id: UUID,
        scope: CapsuleScope,
        scope_reference: str,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Resolve a Capsule instance configuration with overrides.

        Args:
            definition_id: Capsule definition UUID
            tenant_id: Tenant UUID
            scope: Scope type
            scope_reference: Scope reference
            overrides: Optional configuration overrides

        Returns:
            Resolved effective configuration

        Raises:
            ValueError: If definition not found or not ACTIVE
        """
        async with get_async_session() as session:
            stmt = select(CapsuleDefinition).where(
                and_(
                    CapsuleDefinition.id == definition_id,
                    CapsuleDefinition.tenant_id == tenant_id,
                    CapsuleDefinition.status == CapsuleStatus.ACTIVE,
                )
            )
            result = await session.execute(stmt)
            definition = result.scalar_one_or_none()

            if not definition:
                raise ValueError(f"Active Capsule definition {definition_id} not found")

            # Build base configuration from definition
            config = {
                "persona": {
                    "default_persona_ref_id": (
                        str(definition.default_persona_ref_id)
                        if definition.default_persona_ref_id
                        else None
                    ),
                    "role_overrides": definition.role_overrides,
                },
                "tools": {
                    "allowed": definition.allowed_tools,
                    "prohibited": definition.prohibited_tools,
                    "mcp_servers": definition.allowed_mcp_servers,
                    "risk_profile": definition.tool_risk_profile,
                },
                "runtime": {
                    "max_wall_clock_seconds": definition.max_wall_clock_seconds,
                    "max_concurrent_nodes": definition.max_concurrent_nodes,
                    "allowed_runtimes": definition.allowed_runtimes,
                    "resource_profile": definition.resource_profile,
                },
                "network": {
                    "allowed_domains": definition.allowed_domains,
                    "blocked_domains": definition.blocked_domains,
                    "egress_mode": definition.egress_mode.value,
                },
                "policy": {
                    "opa_packages": definition.opa_policy_packages,
                    "guardrails": definition.guardrail_profiles,
                },
                "hitl": {
                    "mode": definition.default_hitl_mode.value,
                    "risk_thresholds": definition.risk_thresholds,
                    "max_pending": definition.max_pending_hitl,
                },
                "rl": {
                    "export_allowed": definition.rl_export_allowed,
                    "export_scope": definition.rl_export_scope.value,
                    "excluded_fields": definition.rl_excluded_fields,
                    "example_store_policy": definition.example_store_policy,
                },
                "compliance": {
                    "data_classification": definition.data_classification.value,
                    "retention_days": definition.retention_policy_days,
                },
            }

            # Apply overrides if provided
            if overrides:
                config = self._deep_merge(config, overrides)

            return config

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge override dict into base dict"""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    async def validate_capsule_against_opa(
        self, capsule_id: UUID, tenant_id: UUID
    ) -> dict[str, Any]:
        """
        Validate Capsule definition against OPA policies.

        Args:
            capsule_id: Capsule UUID
            tenant_id: Tenant UUID

        Returns:
            OPA validation result

        Raises:
            ValueError: If Capsule not found
        """
        capsule = await self.get_definition(capsule_id, tenant_id)

        if not capsule:
            raise ValueError(f"Capsule {capsule_id} not found")

        # TODO: Integrate with real OPA service
        # For now, return synthetic validation result
        # Real implementation will call OPA HTTP API with Capsule JSON

        validation_result = {
            "valid": True,
            "policy_decisions": [],
            "violations": [],
            "warnings": [],
        }

        # Example validation: Check if root permissions are allowed
        # This would be real OPA policy in production
        if capsule.resource_profile.get("root_permissions", False):
            if capsule.name not in ["hacker-quick-scan"]:  # Policy exception
                validation_result["valid"] = False
                validation_result["violations"].append(
                    "Root permissions only allowed for explicitly approved Capsules"
                )

        return validation_result
