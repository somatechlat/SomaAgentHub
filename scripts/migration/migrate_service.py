#!/usr/bin/env python3
"""
Service Migration Script
Automated migration of services to unified configuration
"""

import os
import sys
import shutil
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.common.config.unified_settings import get_settings
from services.common.registry.service_registry import get_service_registry
from services.common.secrets.vault_manager import get_vault_manager


class ServiceMigrator:
    """Automated service migration tool"""
    
    def __init__(self, service_path: str):
        self.service_path = Path(service_path)
        self.service_name = self.service_path.name
        self.settings = get_settings()
        self.registry = get_service_registry()
        self.vault = get_vault_manager()
    
    def find_config_files(self) -> list:
        """Find all config.py files in service"""
        config_files = []
        
        for pattern in ["config.py", "*/config.py", "*/core/config.py"]:
            matches = list(self.service_path.glob(pattern))
            config_files.extend(matches)
        
        return config_files
    
    def analyze_config_usage(self, config_file: Path) -> dict:
        """Analyze how config is used in the service"""
        with open(config_file, 'r') as f:
            content = f.read()
        
        analysis = {
            'file': str(config_file),
            'env_vars': re.findall(r'os\.environ\[\s*["\']([^"\']+)["\']\s*\]', content),
            'os_getenv': re.findall(r'os\.getenv\(["\']([^"\']+)["\'][^)]*\)', content),
            'from_env': re.findall(r'from_env\(["\']([^"\']+)["\'][^)]*\)', content),
            'config_class': bool(re.search(r'class.*Config', content))
        }
        
        return analysis
    
    def generate_migrated_config(self, analysis: dict) -> str:
        """Generate migrated configuration file"""
        template = f'''"""
Unified Configuration for {self.service_name}
Migrated to use centralized settings
"""

from services.common.config.unified_settings import get_settings
from services.common.registry.service_registry import get_service_registry
from services.common.secrets.vault_manager import get_vault_manager
from services.common.deployment.deployment_strategy import get_deployment_config

# Get unified settings
settings = get_settings()
registry = get_service_registry()
vault = get_vault_manager()
deployment_config = get_deployment_config("{self.service_name}")

# Service-specific configuration
SERVICE_NAME = "{self.service_name}"
SERVICE_PORT = settings.service_ports.get("{self.service_name}", 8080)

# Database configuration
DATABASE_URL = deployment_config.database_url
REDIS_URL = deployment_config.redis_url

# Service discovery
SERVICE_REGISTRY = registry

# Secrets management
SECRETS = vault.get_service_secrets(SERVICE_NAME)

# Environment-specific configuration
ENVIRONMENT = settings.environment
DEPLOYMENT_MODE = settings.deployment_mode

# Quick access functions
def get_service_url(service_name: str):
    """Get URL for another service"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(registry.get_service_url(service_name))
    finally:
        loop.close()

# Legacy compatibility
def get_env_var(name: str, default=None):
    """Get environment variable with fallback to settings"""
    return os.getenv(name, getattr(settings, name.lower(), default))
'''
        return template
    
    def migrate_config_file(self, config_file: Path) -> bool:
        """Migrate a single config file"""
        try:
            # Backup original
            backup_path = config_file.with_suffix('.py.backup')
            shutil.copy2(config_file, backup_path)
            
            # Generate migrated content
            analysis = self.analyze_config_usage(config_file)
            migrated_content = self.generate_migrated_config(analysis)
            
            # Write new config
            with open(config_file, 'w') as f:
                f.write(migrated_content)
            
            print(f"✅ Migrated {config_file} -> backup saved as {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to migrate {config_file}: {e}")
            return False
    
    def update_requirements(self) -> bool:
        """Update requirements.txt to include common package"""
        requirements_path = self.service_path / "requirements.txt"
        
        if requirements_path.exists():
            with open(requirements_path, 'r') as f:
                content = f.read()
            
            # Add common package path
            if "services/common" not in content:
                with open(requirements_path, 'a') as f:
                    f.write("\n# Centralized configuration\n-e ../common\n")
                print(f"✅ Updated {requirements_path}")
                return True
        
        return False
    
    def create_env_file(self) -> bool:
        """Create standardized .env file"""
        env_content = f'''# {self.service_name} Environment Configuration
SOMASTACK_ENVIRONMENT=development
SOMASTACK_DEPLOYMENT_MODE=local
SOMASTACK_SERVICE_NAME={self.service_name}
SOMASTACK_SERVICE_PORT={self.settings.service_ports.get(self.service_name, 8080)}

# Database
SOMASTACK_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/{self.service_name}_dev
SOMASTACK_REDIS_URL=redis://localhost:6379

# Service Registry
SOMASTACK_REGISTRY_URL=http://localhost:8080

# Security
SOMASTACK_JWT_SECRET=dev-secret-key-change-in-production

# Monitoring
SOMASTACK_PROMETHEUS_URL=http://localhost:9090
SOMASTACK_GRAFANA_URL=http://localhost:3000
'''
        
        env_path = self.service_path / ".env"
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created {env_path}")
        return True
    
    def migrate_service(self) -> dict:
        """Complete migration of a service"""
        results = {
            'service': self.service_name,
            'config_files': [],
            'status': 'success',
            'errors': []
        }
        
        print(f"🚀 Migrating {self.service_name}...")
        
        # Find config files
        config_files = self.find_config_files()
        
        if not config_files:
            print(f"⚠️ No config.py files found in {self.service_name}")
            results['status'] = 'no_config'
            return results
        
        # Migrate each config file
        for config_file in config_files:
            if self.migrate_config_file(config_file):
                results['config_files'].append(str(config_file))
            else:
                results['errors'].append(str(config_file))
        
        # Update requirements
        self.update_requirements()
        
        # Create .env file
        self.create_env_file()
        
        if results['errors']:
            results['status'] = 'partial'
        
        return results


def migrate_all_services():
    """Migrate all services"""
    services_dir = Path("services")
    
    if not services_dir.exists():
        print("❌ Services directory not found")
        return
    
    results = []
    
    for service_path in services_dir.iterdir():
        if service_path.is_dir() and service_path.name != "common":
            try:
                migrator = ServiceMigrator(str(service_path))
                result = migrator.migrate_service()
                results.append(result)
            except Exception as e:
                results.append({
                    'service': service_path.name,
                    'status': 'error',
                    'errors': [str(e)]
                })
    
    # Print summary
    print("\n📊 Migration Summary:")
    for result in results:
        print(f"{result['service']}: {result['status']}")
        if result['config_files']:
            print(f"  ✅ Config files: {len(result['config_files'])}")
        if result['errors']:
            print(f"  ❌ Errors: {len(result['errors'])}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Migrate specific service
        service_path = f"services/{sys.argv[1]}"
        if os.path.exists(service_path):
            migrator = ServiceMigrator(service_path)
            result = migrator.migrate_service()
            print(f"Migration result: {result}")
        else:
            print(f"❌ Service {sys.argv[1]} not found")
    else:
        # Migrate all services
        migrate_all_services()