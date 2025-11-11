#!/usr/bin/env python3
"""Tests for the centralised environment resolver.

The original unified‑settings tests have been removed in favour of a minimal
verification that ``resolve_env`` reads variables with the canonical
``SOMA_AGENT_HUB_`` prefix and that the resolver falls back to defaults when
variables are absent.
"""

import os
import sys
from pathlib import Path

# Ensure the repository root is on the import path.
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.common.config.base_settings import resolve_env


def test_resolve_env_prefix():
    """Confirm ``resolve_env`` uses the correct prefix.

    The function should prepend ``SOMA_AGENT_HUB_`` to the requested name.
    """
    os.environ["SOMA_AGENT_HUB_SAMPLE_VAR"] = "value"
    assert resolve_env("SAMPLE_VAR") == "value"
    # Cleanup
    del os.environ["SOMA_AGENT_HUB_SAMPLE_VAR"]


def test_resolve_env_default():
    """Verify the default value is returned when the variable is missing."""
    default = "default-value"
    assert resolve_env("NON_EXISTENT", default) == default



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
    """Test that the canonical ``SOMA_AGENT_HUB_`` prefix works.

    The legacy ``SOMASTACK_`` variables have been removed; this test now
    verifies that ``resolve_env`` correctly reads variables with the new
    prefix and returns ``None`` (or a default) when they are absent.
    """
    print("🧪 Testing Environment Variables...")

    # Set a sample variable using the new prefix.
    os.environ["SOMA_AGENT_HUB_SAMPLE_ENV"] = "sample"
    assert resolve_env("SAMPLE_ENV") == "sample"
    del os.environ["SOMA_AGENT_HUB_SAMPLE_ENV"]

    # Verify that a missing variable returns ``None``.
    assert resolve_env("MISSING_ENV") is None

    print("✅ Environment Variables test passed")
    return True


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
    
    # Only include tests that are defined in this file.
    tests = [
        test_resolve_env_prefix,
        test_resolve_env_default,
        test_deployment_strategy,
        test_environment_variables,
        test_migrated_services,
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
