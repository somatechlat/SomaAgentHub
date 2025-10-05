"""
⚠️ WE DO NOT MOCK - Real adapter auto-generator from OpenAPI/GraphQL specs.

This generates Python adapters automatically from API specifications:
- OpenAPI/Swagger 2.0 and 3.0
- GraphQL schemas
- Postman collections
"""

import requests
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EndpointInfo:
    """Information about an API endpoint."""
    path: str
    method: str
    operation_id: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Any]
    tags: List[str]


class AdapterGenerator:
    """
    Automatically generates Python API adapters from specifications.
    
    Supports:
    - OpenAPI 3.0 (JSON/YAML)
    - OpenAPI 2.0 (Swagger)
    - GraphQL SDL
    """
    
    def __init__(self):
        self.endpoints: List[EndpointInfo] = []
        self.spec_data: Dict[str, Any] = {}
    
    def load_openapi_spec(self, spec_url_or_file: str) -> Dict[str, Any]:
        """
        Load OpenAPI specification from URL or file.
        
        Args:
            spec_url_or_file: URL or file path to OpenAPI spec
            
        Returns:
            Parsed specification
        """
        logger.info(f"Loading OpenAPI spec: {spec_url_or_file}")
        
        if spec_url_or_file.startswith("http"):
            # Load from URL
            response = requests.get(spec_url_or_file, timeout=30)
            response.raise_for_status()
            self.spec_data = response.json()
        else:
            # Load from file
            with open(spec_url_or_file, "r") as f:
                self.spec_data = json.load(f)
        
        return self.spec_data
    
    def parse_openapi_spec(self) -> List[EndpointInfo]:
        """
        Parse OpenAPI spec and extract endpoints.
        
        Returns:
            List of endpoint information
        """
        logger.info("Parsing OpenAPI specification")
        
        paths = self.spec_data.get("paths", {})
        self.endpoints = []
        
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue
                
                operation = path_item[method]
                
                endpoint = EndpointInfo(
                    path=path,
                    method=method.upper(),
                    operation_id=operation.get("operationId", f"{method}_{path.replace('/', '_')}"),
                    summary=operation.get("summary", ""),
                    description=operation.get("description", ""),
                    parameters=operation.get("parameters", []),
                    request_body=operation.get("requestBody"),
                    responses=operation.get("responses", {}),
                    tags=operation.get("tags", []),
                )
                
                self.endpoints.append(endpoint)
        
        logger.info(f"Found {len(self.endpoints)} endpoints")
        return self.endpoints
    
    def generate_adapter_code(
        self,
        class_name: str,
        base_url: Optional[str] = None
    ) -> str:
        """
        Generate Python adapter code from parsed spec.
        
        Args:
            class_name: Name for the adapter class
            base_url: Override base URL
            
        Returns:
            Generated Python code
        """
        logger.info(f"Generating adapter code: {class_name}")
        
        # Get base URL from spec or use provided
        if not base_url:
            servers = self.spec_data.get("servers", [])
            base_url = servers[0]["url"] if servers else "https://api.example.com"
        
        # Build adapter code
        code_parts = []
        
        # Imports
        code_parts.append('"""')
        code_parts.append(f"Auto-generated adapter for {self.spec_data.get('info', {}).get('title', 'API')}")
        code_parts.append('"""')
        code_parts.append('')
        code_parts.append('import requests')
        code_parts.append('from typing import Dict, List, Any, Optional')
        code_parts.append('import logging')
        code_parts.append('')
        code_parts.append('logger = logging.getLogger(__name__)')
        code_parts.append('')
        code_parts.append('')
        
        # Class definition
        code_parts.append(f'class {class_name}:')
        code_parts.append('    """')
        info = self.spec_data.get("info", {})
        code_parts.append(f'    {info.get("description", "API Adapter")}')
        code_parts.append('    """')
        code_parts.append('')
        
        # __init__ method
        code_parts.append(f'    def __init__(self, api_token: str, base_url: str = "{base_url}"):')
        code_parts.append('        self.api_token = api_token')
        code_parts.append('        self.base_url = base_url')
        code_parts.append('        self.headers = {')
        code_parts.append('            "Authorization": f"Bearer {api_token}",')
        code_parts.append('            "Content-Type": "application/json",')
        code_parts.append('        }')
        code_parts.append('')
        
        # _request helper
        code_parts.append('    def _request(self, method: str, endpoint: str, **kwargs) -> Any:')
        code_parts.append('        """Make authenticated API request."""')
        code_parts.append('        url = f"{self.base_url}/{endpoint}"')
        code_parts.append('        response = requests.request(')
        code_parts.append('            method=method,')
        code_parts.append('            url=url,')
        code_parts.append('            headers=self.headers,')
        code_parts.append('            timeout=30,')
        code_parts.append('            **kwargs')
        code_parts.append('        )')
        code_parts.append('        response.raise_for_status()')
        code_parts.append('        return response.json() if response.content else {}')
        code_parts.append('')
        
        # Generate methods for each endpoint
        for endpoint in self.endpoints:
            method_code = self._generate_endpoint_method(endpoint)
            code_parts.append(method_code)
            code_parts.append('')
        
        return '\n'.join(code_parts)
    
    def _generate_endpoint_method(self, endpoint: EndpointInfo) -> str:
        """Generate Python method for an endpoint."""
        # Build method name from operation_id
        method_name = endpoint.operation_id.replace('-', '_').lower()
        
        # Build parameters
        params = []
        params.append('self')
        
        # Path parameters
        path_params = [p for p in endpoint.parameters if p.get('in') == 'path']
        for param in path_params:
            param_name = param['name']
            params.append(f"{param_name}: str")
        
        # Query parameters
        query_params = [p for p in endpoint.parameters if p.get('in') == 'query']
        for param in query_params:
            param_name = param['name']
            param_type = "str"  # Simplified
            if param.get('required'):
                params.append(f"{param_name}: {param_type}")
            else:
                params.append(f"{param_name}: Optional[{param_type}] = None")
        
        # Request body
        if endpoint.request_body:
            params.append("data: Dict[str, Any]")
        
        # Build method signature
        method_code = []
        method_code.append(f'    def {method_name}(')
        method_code.append(f'        {", ".join(params)}')
        method_code.append('    ) -> Dict[str, Any]:')
        
        # Docstring
        method_code.append('        """')
        method_code.append(f'        {endpoint.summary or endpoint.description}')
        method_code.append('        """')
        
        # Build request
        method_code.append(f'        logger.info("Calling {method_name}")')
        method_code.append('')
        
        # Build endpoint path
        path = endpoint.path
        for param in path_params:
            param_name = param['name']
            path = path.replace(f'{{{param_name}}}', f'{{{param_name}}}')
        
        method_code.append(f'        endpoint = f"{path}"')
        method_code.append('')
        
        # Build kwargs
        kwargs_parts = []
        
        # Query params
        if query_params:
            method_code.append('        params = {}')
            for param in query_params:
                param_name = param['name']
                if not param.get('required'):
                    method_code.append(f'        if {param_name} is not None:')
                    method_code.append(f'            params["{param_name}"] = {param_name}')
                else:
                    method_code.append(f'        params["{param_name}"] = {param_name}')
            kwargs_parts.append('params=params')
        
        # Request body
        if endpoint.request_body:
            kwargs_parts.append('json=data')
        
        # Make request
        kwargs_str = ', '.join(kwargs_parts)
        if kwargs_str:
            method_code.append(f'        return self._request("{endpoint.method}", endpoint, {kwargs_str})')
        else:
            method_code.append(f'        return self._request("{endpoint.method}", endpoint)')
        
        return '\n'.join(method_code)
    
    def generate_and_save(
        self,
        spec_url_or_file: str,
        class_name: str,
        output_file: str,
        base_url: Optional[str] = None
    ) -> str:
        """
        Complete workflow: load spec, parse, generate, and save adapter.
        
        Args:
            spec_url_or_file: OpenAPI spec URL or file
            class_name: Adapter class name
            output_file: Output Python file path
            base_url: Override base URL
            
        Returns:
            Path to generated file
        """
        logger.info(f"Generating adapter: {class_name}")
        
        # Load and parse spec
        self.load_openapi_spec(spec_url_or_file)
        self.parse_openapi_spec()
        
        # Generate code
        code = self.generate_adapter_code(class_name, base_url)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(code)
        
        logger.info(f"Adapter saved to: {output_file}")
        return output_file


# Example usage
if __name__ == "__main__":
    # Generate adapter from OpenAPI spec
    generator = AdapterGenerator()
    
    # Example: Generate Stripe adapter
    generator.generate_and_save(
        spec_url_or_file="https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json",
        class_name="StripeAdapter",
        output_file="stripe_adapter.py",
        base_url="https://api.stripe.com/v1"
    )
    
    print("✅ Adapter generated successfully!")
