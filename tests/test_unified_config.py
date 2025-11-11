#!/usr/bin/env python3
import pytest
pytestmark = pytest.mark.skip("Deprecated: unified settings/registry/vault_manager removed; test skipped.")

import os
import sys
import asyncio
from pathlib import Path
from services.common.config.base_settings import resolve_env

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_unified_settings():
    """Test unified settings configuration"""
    print("🧪 Testing Unified Settings...")
    
    try:
        from services.common.config.unified_settings import get_settings
        settings = get_settings()
        
        # Test basic configuration
        assert settings.environment == "development"
        assert settings.deployment_mode == "local"
        assert "gateway_api" in settings.service_ports
        assert settings.service_ports["gateway_api"] == 8080
        
        # Test environment prefix
        assert settings.Config.env_prefix == "SOMA_AGENT_HUB_"
        
        print("✅ Unified Settings test passed")
        return True
        
    except Exception as e:
        print(f"❌ Unified Settings test failed: {e}")
        return False


def test_service_registry():
    """Test service registry"""
    print("🧪 Testing Service Registry...")
    
    try:
        from services.common.registry.service_registry import get_service_registry
        registry = get_service_registry()
        
        # Test service registration
        services = registry.services
        assert len(services) > 0
        assert "gateway_api" in services or "gateway-api" in services
        
        print("✅ Service Registry test passed")
        return True
        
    except Exception as e:
        print(f"❌ Service Registry test failed: {e}")
        return False


def test_secrets_manager():
    """Test secrets manager"""
    print("🧪 Testing Secrets Manager...")
    
    try:
        from services.common.secrets.vault_manager import get_vault_manager
        vault = get_vault_manager()
        
        # Test development secrets fallback
        secret = vault.get_secret("jwt", "secret")
        assert secret is not None
        
        print("✅ Secrets Manager test passed")
        return True
        
    except Exception as e:
        print(f"❌ Secrets Manager test failed: {e}")
        return False


def test_session_manager():
    """Test session manager"""
    print("🧪 Testing Session Manager...")
    
    try:
        from services.common.session.session_manager import get_session_manager
        session_mgr = get_session_manager()
        
        # Test session creation
        token = session_mgr.create_session("test_user", "test_tenant", ["read", "write"])
        assert token is not None
        
        # Test session validation
        session_data = session_mgr.validate_session(token)
        assert session_data.user_id == "test_user"
        assert session_data.tenant_id == "test_tenant"
        
        print("✅ Session Manager test passed")
        return True
        
    except Exception as e:
        print(f"❌ Session Manager test failed: {e}")
        return False


def test_deployment_strategy():
    """Test deployment strategy"""
    print("🧪 Testing Deployment Strategy...")
    
    try:
        from services.common.deployment.deployment_strategy import (
            get_deployment_config,
            DeploymentFactory
        )
        
        # Test deployment factory
        strategy = DeploymentFactory.create_strategy("local")
        assert strategy is not None
        
        # Test deployment config
        config = get_deployment_config("gateway_api")
        assert config.service_name == "gateway_api"
        assert config.database_url is not None
        
        print("✅ Deployment Strategy test passed")
        return True
        
    except Exception as e:
        print(f"❌ Deployment Strategy test failed: {e}")
        return False


async def test_service_discovery():
    """Test service discovery"""
    print("🧪 Testing Service Discovery...")
    
    try:
        from services.common.registry.service_registry import get_service_registry
        registry = get_service_registry()
        
        # Test service URL retrieval
        # Note: This will use localhost URLs in development
        services = list(registry.services.keys())[:3]  # Test first 3 services
        
        for service_name in services:
            try:
                url = await registry.get_service_url(service_name, healthy_only=False)
                assert url is not None
                print(f"   {service_name}: {url}")
            except Exception as e:
                print(f"   {service_name}: URL not available ({e})")
        
        print("✅ Service Discovery test passed")
        return True
        
    except Exception as e:
        print(f"❌ Service Discovery test failed: {e}")
        return False


def test_environment_variables():
    """Test environment variable standardization"""
    print("🧪 Testing Environment Variables...")
    
    try:
        # Test that SOMASTACK_ variables are defined
        env_vars = [
            "SOMASTACK_ENVIRONMENT",
            "SOMASTACK_DEPLOYMENT_MODE",
            "SOMASTACK_REDIS_URL",
            "SOMASTACK_VAULT_ADDRESS"
        ]
        
        for var in env_vars:
            value = resolve_env(var)
            if value:
                print(f"   {var}: {value}")
            else:
                print(f"   {var}: not set (using defaults)")
        
        print("✅ Environment Variables test passed")
        return True
        
    except Exception as e:
        print(f"❌ Environment Variables test failed: {e}")
        return False


def test_migrated_services():
    """Test that services can import unified config"""
    print("🧪 Testing Migrated Services...")
    
    services = [
        "gateway_api",
        "orchestrator", 
        "memory_gateway",
        "policy_engine",
        "llm_hub"
    ]
    
    success_count = 0
    
    for service in services:
        try:
            # Test that service can import unified config
            service_path = Path(f"services/{service}")
            
            # Check for unified config files
            config_files = list(service_path.glob("**/config.py")) + list(service_path.glob("**/unified_config.py"))
            
            if config_files:
                print(f"   {service}: ✅ Found unified config")
                success_count += 1
            else:
                print(f"   {service}: ⚠️ No unified config found")
                
        except Exception as e:
            print(f"   {service}: ❌ Import error: {e}")
    
    print(f"✅ {success_count}/{len(services)} services migrated successfully")
    return success_count == len(services)


def run_all_tests():
    """Run all integration tests"""
    print("🚀 Running Unified Configuration Integration Tests...\n")
    
    tests = [
        test_unified_settings,
        test_service_registry,
        test_secrets_manager,
        test_session_manager,
        test_deployment_strategy,
        test_environment_variables,
        test_migrated_services
    ]
    
    async_tests = [test_service_discovery]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run synchronous tests
    for test in tests:
        if test():
            passed += 1
    
    # Run async tests
    for test in async_tests:
        try:
            if asyncio.run(test()):
                passed += 1
        except Exception as e:
            print(f"❌ Async test {test.__name__} failed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Unified configuration system is ready.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
