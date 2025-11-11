"""
⚠️ WE DO NOT MOCK - Real Terraform adapter for infrastructure as code.

Provides comprehensive Terraform integration:
- Plan and apply infrastructure
- State management
- Workspace operations
- Variable injection
- Output parsing
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any
from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


class TerraformAdapter:
    """
    Adapter for Terraform CLI operations.

    Terraform Documentation: https://www.terraform.io/docs
    """

    def __init__(
        self,
        working_dir: str,
        terraform_bin: str = "terraform",
        auto_approve: bool = False,
    ):
        """
        Initialize Terraform adapter.

        Args:
            working_dir: Directory containing Terraform files
            terraform_bin: Path to terraform binary
            auto_approve: Auto-approve applies (use with caution!)
        """
        self.working_dir = Path(working_dir)
        self.terraform_bin = terraform_bin
        self.auto_approve = auto_approve

        # Ensure working directory exists
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def _run_command(
        self,
        args: list[str],
        capture_output: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """
        Run terraform command.

        Args:
            args: Command arguments
            capture_output: Capture stdout/stderr
            env: Environment variables

        Returns:
            Completed process
        """
        cmd = [self.terraform_bin] + args

        logger.info(f"Running Terraform: {' '.join(cmd)}")

        # Merge environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        result = subprocess.run(
            cmd,
            cwd=str(self.working_dir),
            capture_output=capture_output,
            text=True,
            env=process_env,
            check=True,
        )

        return result

    # Core Terraform Operations

    def init(
        self,
        backend_config: dict[str, str] | None = None,
        upgrade: bool = False,
        reconfigure: bool = False,
    ) -> str:
        """
        Initialize Terraform working directory.

        Args:
            backend_config: Backend configuration
            upgrade: Upgrade modules and plugins
            reconfigure: Reconfigure backend

        Returns:
            Command output
        """
        logger.info("Initializing Terraform")

        args = ["init"]

        if backend_config:
            for key, value in backend_config.items():
                args.extend(["-backend-config", f"{key}={value}"])

        if upgrade:
            args.append("-upgrade")

        if reconfigure:
            args.append("-reconfigure")

        result = self._run_command(args)
        return result.stdout

    def plan(
        self,
        var_file: str | None = None,
        variables: dict[str, Any] | None = None,
        out_file: str | None = None,
        target: list[str] | None = None,
        destroy: bool = False,
    ) -> str:
        """
        Create execution plan.

        Args:
            var_file: Path to variables file
            variables: Variables dict
            out_file: Save plan to file
            target: Specific resources to target
            destroy: Create destroy plan

        Returns:
            Plan output
        """
        logger.info("Creating Terraform plan")

        args = ["plan"]

        if var_file:
            args.extend(["-var-file", var_file])

        if variables:
            for key, value in variables.items():
                args.extend(["-var", f"{key}={value}"])

        if out_file:
            args.extend(["-out", out_file])

        if target:
            for resource in target:
                args.extend(["-target", resource])

        if destroy:
            args.append("-destroy")

        result = self._run_command(args)
        return result.stdout

    def apply(
        self,
        plan_file: str | None = None,
        var_file: str | None = None,
        variables: dict[str, Any] | None = None,
        target: list[str] | None = None,
        auto_approve: bool | None = None,
    ) -> str:
        """
        Apply Terraform changes.

        Args:
            plan_file: Saved plan file
            var_file: Variables file
            variables: Variables dict
            target: Specific resources
            auto_approve: Override default auto_approve

        Returns:
            Apply output
        """
        logger.info("Applying Terraform changes")

        args = ["apply"]

        # Auto-approve
        should_approve = auto_approve if auto_approve is not None else self.auto_approve
        if should_approve:
            args.append("-auto-approve")

        if plan_file:
            args.append(plan_file)
        else:
            if var_file:
                args.extend(["-var-file", var_file])

            if variables:
                for key, value in variables.items():
                    args.extend(["-var", f"{key}={value}"])

            if target:
                for resource in target:
                    args.extend(["-target", resource])

        result = self._run_command(args)
        return result.stdout

    def destroy(
        self,
        var_file: str | None = None,
        variables: dict[str, Any] | None = None,
        target: list[str] | None = None,
        auto_approve: bool | None = None,
    ) -> str:
        """
        Destroy Terraform-managed infrastructure.

        Args:
            var_file: Variables file
            variables: Variables dict
            target: Specific resources
            auto_approve: Override default auto_approve

        Returns:
            Destroy output
        """
        logger.info("Destroying Terraform infrastructure")

        args = ["destroy"]

        should_approve = auto_approve if auto_approve is not None else self.auto_approve
        if should_approve:
            args.append("-auto-approve")

        if var_file:
            args.extend(["-var-file", var_file])

        if variables:
            for key, value in variables.items():
                args.extend(["-var", f"{key}={value}"])

        if target:
            for resource in target:
                args.extend(["-target", resource])

        result = self._run_command(args)
        return result.stdout

    # State Management

    def show(self, json_output: bool = True) -> Any:
        """
        Show current state or plan.

        Args:
            json_output: Output as JSON

        Returns:
            State data (dict if JSON, str otherwise)
        """
        args = ["show"]

        if json_output:
            args.append("-json")

        result = self._run_command(args)

        if json_output:
            return json.loads(result.stdout)
        return result.stdout

    def state_list(self) -> list[str]:
        """List resources in state."""
        result = self._run_command(["state", "list"])
        return [line.strip() for line in result.stdout.split("\n") if line.strip()]

    def state_show(self, resource: str) -> str:
        """Show specific resource in state."""
        result = self._run_command(["state", "show", resource])
        return result.stdout

    def state_rm(self, resource: str) -> str:
        """Remove resource from state."""
        logger.warning(f"Removing resource from state: {resource}")
        result = self._run_command(["state", "rm", resource])
        return result.stdout

    def state_mv(self, source: str, destination: str) -> str:
        """Move resource in state."""
        result = self._run_command(["state", "mv", source, destination])
        return result.stdout

    def state_pull(self) -> dict[str, Any]:
        """Pull current state."""
        result = self._run_command(["state", "pull"])
        return json.loads(result.stdout)

    def state_push(self, state_file: str) -> str:
        """Push state file."""
        logger.warning("Pushing state file - use with extreme caution!")
        result = self._run_command(["state", "push", state_file])
        return result.stdout

    # Workspace Management

    def workspace_list(self) -> list[str]:
        """List workspaces."""
        result = self._run_command(["workspace", "list"])
        workspaces = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line:
                # Remove * from current workspace
                workspace = line.replace("*", "").strip()
                workspaces.append(workspace)
        return workspaces

    def workspace_new(self, name: str) -> str:
        """Create new workspace."""
        logger.info(f"Creating workspace: {name}")
        result = self._run_command(["workspace", "new", name])
        return result.stdout

    def workspace_select(self, name: str) -> str:
        """Select workspace."""
        logger.info(f"Selecting workspace: {name}")
        result = self._run_command(["workspace", "select", name])
        return result.stdout

    def workspace_delete(self, name: str) -> str:
        """Delete workspace."""
        logger.warning(f"Deleting workspace: {name}")
        result = self._run_command(["workspace", "delete", name])
        return result.stdout

    # Output Management

    def output(self, name: str | None = None, json_output: bool = True) -> Any:
        """
        Get output values.

        Args:
            name: Specific output name
            json_output: Return as JSON

        Returns:
            Output value(s)
        """
        args = ["output"]

        if json_output:
            args.append("-json")

        if name:
            args.append(name)

        result = self._run_command(args)

        if json_output:
            data = json.loads(result.stdout)
            # If specific output, return just the value
            if name and isinstance(data, dict):
                return data.get("value")
            return data

        return result.stdout.strip()

    # Validation and Formatting

    def validate(self) -> str:
        """Validate Terraform configuration."""
        logger.info("Validating Terraform configuration")
        result = self._run_command(["validate"])
        return result.stdout

    def fmt(self, check: bool = False, recursive: bool = True) -> str:
        """
        Format Terraform files.

        Args:
            check: Check if files are formatted
            recursive: Format recursively

        Returns:
            Format output
        """
        args = ["fmt"]

        if check:
            args.append("-check")

        if recursive:
            args.append("-recursive")

        result = self._run_command(args)
        return result.stdout

    # Utility Methods

    def create_backend_config(self, backend_type: str, config: dict[str, str]) -> str:
        """
        Create backend configuration file.

        Args:
            backend_type: Backend type (s3, azurerm, gcs, etc.)
            config: Backend configuration

        Returns:
            Path to backend config file
        """
        backend_hcl = f'terraform {{\n  backend "{backend_type}" {{\n'

        for key, value in config.items():
            backend_hcl += f'    {key} = "{value}"\n'

        backend_hcl += "  }\n}\n"

        backend_file = self.working_dir / "backend.tf"
        backend_file.write_text(backend_hcl)

        logger.info(f"Created backend config: {backend_file}")
        return str(backend_file)

    def plan_and_apply(
        self, variables: dict[str, Any] | None = None, auto_approve: bool = False
    ) -> dict[str, str]:
        """
        Convenience method: plan and apply in one call.

        Args:
            variables: Terraform variables
            auto_approve: Auto-approve apply

        Returns:
            Dict with plan and apply outputs
        """
        logger.info("Running plan and apply")

        # Create plan
        plan_file = "tfplan"
        plan_output = self.plan(variables=variables, out_file=plan_file)

        # Apply plan
        apply_output = self.apply(plan_file=plan_file, auto_approve=auto_approve)

        return {"plan": plan_output, "apply": apply_output}
