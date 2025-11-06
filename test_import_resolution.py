#!/usr/bin/env python3
"""Test script to verify import resolution fixes from the problem statement.

This script tests that all the import issues mentioned in the problem statement
have been resolved:
1. app.core.bus with get_notification_bus function
2. app.constitution_cache exposing get_cached_hash and invalidate_hash
3. services.marketplace.app.db implementing get_db
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

def test_app_core_bus():
    """Test that app.core.bus module exists and exposes get_notification_bus."""
    try:
        from app.core.bus import get_notification_bus
        print("✓ app.core.bus.get_notification_bus import successful")
        assert callable(get_notification_bus), "get_notification_bus should be callable"
        print("✓ get_notification_bus is callable")
        return True
    except ImportError as e:
        print(f"✗ Failed to import app.core.bus: {e}")
        return False

def test_app_constitution_cache():
    """Test that app.constitution_cache module exists and exposes required functions."""
    try:
        from app.constitution_cache import get_cached_hash, invalidate_hash
        print("✓ app.constitution_cache imports successful")
        assert callable(get_cached_hash), "get_cached_hash should be callable"
        assert callable(invalidate_hash), "invalidate_hash should be callable"
        print("✓ get_cached_hash and invalidate_hash are callable")
        return True
    except ImportError as e:
        print(f"✗ Failed to import app.constitution_cache: {e}")
        return False

def test_marketplace_db():
    """Test that services.marketplace.app.db module exists and implements get_db."""
    try:
        from services.marketplace.app.db import get_db, Capsule, CapsuleVersion, CapsuleRating, CapsuleDownload
        print("✓ services.marketplace.app.db imports successful")
        assert callable(get_db), "get_db should be callable"
        print("✓ get_db is callable")
        print("✓ Database models (Capsule, CapsuleVersion, CapsuleRating, CapsuleDownload) imported")
        return True
    except ImportError as e:
        print(f"✗ Failed to import services.marketplace.app.db: {e}")
        return False

def test_app_core_constitution():
    """Test that app.core.constitution module exists and exposes verify_bundle."""
    try:
        from app.core.constitution import verify_bundle, ConstitutionVerificationError
        print("✓ app.core.constitution imports successful")
        assert callable(verify_bundle), "verify_bundle should be callable"
        print("✓ verify_bundle is callable")
        return True
    except ImportError as e:
        print(f"✗ Failed to import app.core.constitution: {e}")
        return False

def main():
    """Run all import tests."""
    print("=" * 70)
    print("Testing import resolution fixes")
    print("=" * 70)
    print()
    
    results = []
    
    print("1. Testing app.core.bus module:")
    results.append(test_app_core_bus())
    print()
    
    print("2. Testing app.constitution_cache module:")
    results.append(test_app_constitution_cache())
    print()
    
    print("3. Testing services.marketplace.app.db module:")
    results.append(test_marketplace_db())
    print()
    
    print("4. Testing app.core.constitution module:")
    results.append(test_app_core_constitution())
    print()
    
    print("=" * 70)
    if all(results):
        print("✓ All import resolution tests PASSED")
        print("=" * 70)
        return 0
    else:
        print("✗ Some import resolution tests FAILED")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
