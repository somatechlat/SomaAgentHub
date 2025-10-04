#!/usr/bin/env python3
"""
Comprehensive dependency analysis and fix script for SomaAgent services
"""

import os
import subprocess
import sys
from pathlib import Path

def analyze_python_imports(service_path):
    """Analyze Python files for import statements"""
    imports = set()
    app_path = service_path / "app"
    
    if not app_path.exists():
        return imports
    
    for py_file in app_path.rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                
            # Extract import statements
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    if 'import' in line:
                        # Extract module names
                        if line.startswith('import '):
                            module = line.split('import ')[1].split(' as ')[0].split(',')[0].strip()
                            imports.add(module.split('.')[0])
                        elif line.startswith('from '):
                            module = line.split('from ')[1].split(' import')[0].strip()
                            imports.add(module.split('.')[0])
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return imports

def get_requirements_packages(requirements_file):
    """Get packages from requirements.txt"""
    packages = set()
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    package = line.split('>=')[0].split('==')[0].split('[')[0]
                    packages.add(package)
    return packages

def suggest_missing_packages(imports, existing_packages):
    """Suggest missing packages based on common import-to-package mappings"""
    package_mapping = {
        'aiokafka': 'aiokafka>=0.11.0',
        'kafka': 'kafka-python>=2.0.0', 
        'prometheus_client': 'prometheus-client>=0.20.0',
        'prometheus_fastapi_instrumentator': 'prometheus-fastapi-instrumentator>=7.0.0',
        'redis': 'redis[asyncio]>=5.0.0',
        'httpx': 'httpx>=0.27.0',
        'fastapi': 'fastapi>=0.110.0',
        'uvicorn': 'uvicorn[standard]>=0.29.0',
        'pydantic': 'pydantic>=2.0.0',
        'pydantic_settings': 'pydantic-settings>=2.2.0',
        'sqlalchemy': 'sqlalchemy[asyncio]>=2.0.0',
        'asyncpg': 'asyncpg>=0.29.0',
        'pyjwt': 'pyjwt>=2.8.0',
        'cryptography': 'cryptography>=42.0.0',
        'stripe': 'stripe>=7.0.0',
        'pyyaml': 'pyyaml>=6.0.0',
        'opentelemetry': 'opentelemetry-instrumentation-fastapi>=0.48b0',
        'psycopg2': 'psycopg2-binary>=2.9.0',
        'bcrypt': 'bcrypt>=4.0.0',
        'jose': 'python-jose>=3.3.0',
        'passlib': 'passlib>=1.7.4'
    }
    
    suggestions = []
    for imp in imports:
        if imp in package_mapping:
            package_name = package_mapping[imp].split('>=')[0].split('==')[0]
            if package_name not in existing_packages and imp not in existing_packages:
                suggestions.append(package_mapping[imp])
    
    return suggestions

def analyze_service(service_name, base_path):
    """Analyze a single service for dependency issues"""
    service_path = base_path / "services" / service_name
    requirements_file = service_path / "requirements.txt"
    
    if not service_path.exists():
        return None
    
    print(f"\n🔍 Analyzing {service_name}...")
    
    # Get imports and existing packages
    imports = analyze_python_imports(service_path)
    existing_packages = get_requirements_packages(requirements_file)
    
    # Get suggestions
    suggestions = suggest_missing_packages(imports, existing_packages)
    
    result = {
        'service': service_name,
        'path': service_path,
        'requirements_file': requirements_file,
        'imports': imports,
        'existing_packages': existing_packages,
        'suggested_additions': suggestions,
        'needs_update': len(suggestions) > 0
    }
    
    if suggestions:
        print(f"   📦 Found {len(suggestions)} missing dependencies:")
        for suggestion in suggestions:
            print(f"      + {suggestion}")
    else:
        print(f"   ✅ No obvious missing dependencies")
    
    return result

def update_requirements_file(analysis):
    """Update requirements.txt file with missing dependencies"""
    if not analysis['needs_update']:
        return False
    
    requirements_file = analysis['requirements_file']
    
    # Read existing content
    existing_content = ""
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            existing_content = f.read().strip()
    
    # Add new packages
    new_content = existing_content
    for package in analysis['suggested_additions']:
        if package not in existing_content:
            new_content += f"\n{package}"
    
    # Write updated content
    with open(requirements_file, 'w') as f:
        f.write(new_content.strip() + "\n")
    
    print(f"   ✅ Updated {requirements_file}")
    return True

def main():
    base_path = Path("/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaagent")
    
    services = [
        "analytics-service", "billing-service", "constitution-service", 
        "gateway-api", "identity-service", "jobs", "memory-gateway",
        "orchestrator", "policy-engine", "settings-service", 
        "slm-service", "task-capsule-repo"
    ]
    
    print("🚀 SomaAgent Dependency Analysis and Fix Tool")
    print("=" * 60)
    
    all_analyses = []
    services_needing_updates = []
    
    # Analyze all services
    for service in services:
        analysis = analyze_service(service, base_path)
        if analysis:
            all_analyses.append(analysis)
            if analysis['needs_update']:
                services_needing_updates.append(analysis)
    
    # Summary
    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"   Total services analyzed: {len(all_analyses)}")
    print(f"   Services needing updates: {len(services_needing_updates)}")
    
    if not services_needing_updates:
        print("   🎉 All services have complete dependencies!")
        return
    
    # Ask for confirmation to update
    print(f"\n💡 RECOMMENDED ACTIONS:")
    for analysis in services_needing_updates:
        print(f"   📦 {analysis['service']}: Add {len(analysis['suggested_additions'])} packages")
    
    if input("\nApply all recommended dependency updates? (y/N): ").lower() == 'y':
        print("\n🔧 APPLYING UPDATES...")
        for analysis in services_needing_updates:
            update_requirements_file(analysis)
        
        print(f"\n✅ Updated {len(services_needing_updates)} services")
        print("\nNext steps:")
        print("1. 🏗️  Rebuild Docker images")
        print("2. 📦 Load images into kind cluster")
        print("3. 🔄 Restart deployments")
        print("4. ✅ Run health checks")
    else:
        print("\n❌ No changes applied")

if __name__ == "__main__":
    main()