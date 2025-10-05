"""
⚠️ WE DO NOT MOCK - Tool Adapter Registry.

Central registry for all tool adapters in the ecosystem:
- Dynamic adapter loading
- Capability discovery
- Version management
- Health checks
"""

from typing import Dict, List, Any, Optional, Type
import importlib
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ToolCapability:
    """A single tool capability."""
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: str


@dataclass
class ToolInfo:
    """Information about a registered tool."""
    name: str
    adapter_class: str
    category: str
    capabilities: List[ToolCapability]
    version: str
    requires_auth: bool
    auth_type: str  # api_token, oauth, basic_auth


class ToolRegistry:
    """
    Central registry for all tool adapters.
    
    Provides dynamic loading, discovery, and invocation of tool adapters.
    """
    
    def __init__(self, adapters_dir: str = "services/tool-service/adapters"):
        self.adapters_dir = Path(adapters_dir)
        self.tools: Dict[str, ToolInfo] = {}
        self.loaded_adapters: Dict[str, Any] = {}
        
        # Auto-discover adapters
        self._discover_adapters()
    
    def _discover_adapters(self) -> None:
        """Automatically discover and register adapters."""
        logger.info(f"Discovering adapters in: {self.adapters_dir}")
        
        # Manually register known adapters
        self._register_builtin_adapters()
    
    def _register_builtin_adapters(self) -> None:
        """Register built-in adapters."""
        
        # Project Management
        self.register(ToolInfo(
            name="plane",
            adapter_class="adapters.plane_adapter.PlaneAdapter",
            category="project_management",
            capabilities=[
                ToolCapability("create_project", "Create new project", {"name": "str"}, "project_id"),
                ToolCapability("create_issue", "Create issue", {"title": "str", "description": "str"}, "issue_id"),
                ToolCapability("create_cycle", "Create sprint cycle", {"name": "str"}, "cycle_id"),
            ],
            version="1.0.0",
            requires_auth=True,
            auth_type="api_token"
        ))
        
        self.register(ToolInfo(
            name="jira",
            adapter_class="adapters.jira_adapter.JiraAdapter",
            category="project_management",
            capabilities=[
                ToolCapability("create_issue", "Create Jira issue", {"summary": "str"}, "issue_key"),
                ToolCapability("create_sprint", "Create sprint", {"name": "str"}, "sprint_id"),
            ],
            version="1.0.0",
            requires_auth=True,
            auth_type="api_token"
        ))
        
        # Code & Repositories
        self.register(ToolInfo(
            name="github",
            adapter_class="adapters.github_adapter.GitHubAdapter",
            category="code_repository",
            capabilities=[
                ToolCapability("create_repository", "Create repo", {"name": "str"}, "repo_url"),
                ToolCapability("create_pull_request", "Create PR", {"title": "str"}, "pr_number"),
                ToolCapability("trigger_workflow", "Trigger GitHub Action", {"workflow_id": "str"}, "run_id"),
            ],
            version="1.0.0",
            requires_auth=True,
            auth_type="api_token"
        ))
        
        # Documentation
        self.register(ToolInfo(
            name="notion",
            adapter_class="adapters.notion_adapter.NotionAdapter",
            category="documentation",
            capabilities=[
                ToolCapability("create_page", "Create page", {"title": "str"}, "page_id"),
                ToolCapability("create_database", "Create database", {"title": "str"}, "database_id"),
            ],
            version="1.0.0",
            requires_auth=True,
            auth_type="api_token"
        ))
        
        # Communication
        self.register(ToolInfo(
            name="slack",
            adapter_class="adapters.slack_adapter.SlackAdapter",
            category="communication",
            capabilities=[
                ToolCapability("send_message", "Send message", {"channel": "str", "text": "str"}, "timestamp"),
                ToolCapability("create_channel", "Create channel", {"name": "str"}, "channel_id"),
            ],
            version="1.0.0",
            requires_auth=True,
            auth_type="api_token"
        ))
        
        # Infrastructure
        self.register(ToolInfo(
            name="terraform",
            adapter_class="adapters.terraform_adapter.TerraformAdapter",
            category="infrastructure",
            capabilities=[
                ToolCapability("plan", "Create plan", {}, "plan_output"),
                ToolCapability("apply", "Apply changes", {}, "apply_output"),
            ],
            version="1.0.0",
            requires_auth=False,
            auth_type="none"
        ))
        
        self.register(ToolInfo(
            name="aws",
            adapter_class="adapters.aws_adapter.AWSAdapter",
            category="cloud_services",
            capabilities=[
                ToolCapability("create_s3_bucket", "Create S3 bucket", {"bucket_name": "str"}, "bucket_arn"),
                ToolCapability("create_lambda_function", "Create Lambda", {"function_name": "str"}, "function_arn"),
            ],
            version="1.0.0",
            requires_auth=True,
            auth_type="api_key"
        ))
        
        self.register(ToolInfo(
            name="kubernetes",
            adapter_class="adapters.kubernetes_adapter.KubernetesAdapter",
            category="container_orchestration",
            capabilities=[
                ToolCapability("create_deployment", "Create deployment", {"name": "str", "image": "str"}, "deployment"),
                ToolCapability("create_service", "Create service", {"name": "str"}, "service"),
            ],
            version="1.0.0",
            requires_auth=True,
            auth_type="kubeconfig"
        ))
        
        # UI Automation
        self.register(ToolInfo(
            name="playwright",
            adapter_class="adapters.playwright_adapter.PlaywrightAdapter",
            category="ui_automation",
            capabilities=[
                ToolCapability("automate_workflow", "Automate UI workflow", {"url": "str", "steps": "list"}, "results"),
            ],
            version="1.0.0",
            requires_auth=False,
            auth_type="none"
        ))
        
        logger.info(f"Registered {len(self.tools)} built-in adapters")
    
    def register(self, tool_info: ToolInfo) -> None:
        """Register a tool adapter."""
        self.tools[tool_info.name] = tool_info
        logger.debug(f"Registered tool: {tool_info.name}")
    
    def get_adapter(self, tool_name: str, credentials: Optional[Dict[str, str]] = None) -> Any:
        """
        Get initialized adapter instance.
        
        Args:
            tool_name: Tool name
            credentials: Authentication credentials
            
        Returns:
            Adapter instance
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_info = self.tools[tool_name]
        
        # Check if already loaded
        cache_key = f"{tool_name}:{hash(str(credentials))}"
        if cache_key in self.loaded_adapters:
            return self.loaded_adapters[cache_key]
        
        # Import adapter class
        module_path, class_name = tool_info.adapter_class.rsplit(".", 1)
        module = importlib.import_module(module_path)
        adapter_class = getattr(module, class_name)
        
        # Initialize with credentials
        if tool_info.requires_auth and not credentials:
            raise ValueError(f"Tool {tool_name} requires authentication")
        
        if credentials:
            adapter = adapter_class(**credentials)
        else:
            adapter = adapter_class()
        
        # Cache
        self.loaded_adapters[cache_key] = adapter
        
        logger.info(f"Loaded adapter: {tool_name}")
        return adapter
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolInfo]:
        """
        List available tools.
        
        Args:
            category: Filter by category
            
        Returns:
            List of tool info
        """
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        return tools
    
    def get_capabilities(self, tool_name: str) -> List[ToolCapability]:
        """Get tool capabilities."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return self.tools[tool_name].capabilities
    
    def invoke(
        self,
        tool_name: str,
        capability: str,
        parameters: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Invoke a tool capability.
        
        Args:
            tool_name: Tool name
            capability: Capability name
            parameters: Parameters
            credentials: Auth credentials
            
        Returns:
            Capability result
        """
        logger.info(f"Invoking {tool_name}.{capability}")
        
        # Get adapter
        adapter = self.get_adapter(tool_name, credentials)
        
        # Get method
        method = getattr(adapter, capability)
        
        # Invoke
        result = method(**parameters)
        
        return result
    
    def health_check(self, tool_name: str, credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Check tool health/connectivity.
        
        Args:
            tool_name: Tool name
            credentials: Auth credentials
            
        Returns:
            Health status
        """
        try:
            adapter = self.get_adapter(tool_name, credentials)
            
            # Try a simple operation
            if hasattr(adapter, "health_check"):
                result = adapter.health_check()
                return {"status": "healthy", "details": result}
            
            return {"status": "healthy", "message": "Adapter loaded successfully"}
        
        except Exception as e:
            logger.error(f"Health check failed for {tool_name}: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Global registry instance
tool_registry = ToolRegistry()


# Example usage
if __name__ == "__main__":
    registry = ToolRegistry()
    
    # List all tools
    print(f"Available tools: {len(registry.list_tools())}")
    
    for tool in registry.list_tools():
        print(f"\n{tool.name} ({tool.category})")
        print(f"  Capabilities: {len(tool.capabilities)}")
        for cap in tool.capabilities:
            print(f"    - {cap.name}: {cap.description}")
    
    # Invoke a capability
    # result = registry.invoke(
    #     "github",
    #     "create_repository",
    #     {"name": "test-repo"},
    #     {"token": "ghp_xxx"}
    # )
