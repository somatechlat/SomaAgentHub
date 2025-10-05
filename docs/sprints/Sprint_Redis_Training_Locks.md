# Sprint: Redis Training Mode Locks

**Date:** October 5, 2025  
**Objective**: Replace in-memory training locks with Redis-backed persistence and proper admin capability checks.

## Current State
- ✅ Training mode API endpoints exist
- ✅ Audit events emitted to Kafka
- ❌ Using in-memory dict (`_training_locks: dict[str, dict] = {}`)
- ❌ No Redis persistence
- ❌ No admin capability validation
- ❌ No TTL on locks

## Tasks

### 1. Redis Client Integration
- Add `redis.asyncio` client to training service
- Implement connection pooling
- Add health checks
- Handle connection failures gracefully

### 2. Lock State Persistence
- Replace in-memory dict with Redis keys
- Use `training:lock:{tenant}` key pattern
- Implement TTL (default 24 hours)
- Add lock renewal endpoint

### 3. Admin Capability Checks
- Wire identity-service client
- Validate admin JWT claims before lock operations
- Return 403 for non-admin users
- Emit authorization failures to audit log

### 4. Lock State Queries
- Add GET endpoint to check lock status
- List all active training locks (admin only)
- Add force-unlock capability (super-admin)

## Files to Modify
- `services/orchestrator/app/api/training.py` (replace dict with Redis)
- `services/common/redis_client.py` (create new shared Redis helper)
- Add dependency: `redis[asyncio]>=5.0.0`

## Redis Key Schema
```
training:lock:{tenant_id}
  {
    "enabled": true,
    "locked_by": "user-123",
    "locked_at": 1696516800,
    "reason": "Production deployment freeze",
    "ttl": 86400
  }
```

## Environment Variables
```bash
export REDIS_URL="redis://redis:6379/0"
export TRAINING_LOCK_TTL_SECONDS="86400"
```

## Success Criteria
- ✅ Training locks survive service restarts
- ✅ TTL auto-expires stale locks
- ✅ Admin checks prevent unauthorized locks
- ✅ Metrics track active training sessions
- ✅ No in-memory dict remains

## Owner
Platform team

## Status
**Not started** – TODO comments in training.py
