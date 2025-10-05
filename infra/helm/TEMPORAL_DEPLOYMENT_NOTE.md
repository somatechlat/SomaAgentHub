# Temporal Deployment Note for Sprint-5

## Status: Deferred to Alternative Approach

**Date:** October 5, 2025  
**Decision:** Use Temporal Cloud or Docker Compose for Sprint-5 development

### Issue
Temporal Helm chart has complex configuration requirements:
- Requires specific database schema setup
- Image compatibility issues with admin-tools
- Complex persistence configuration options

### Immediate Solution
For Sprint-5 KAMACHIQ development, use one of:

1. **Temporal Cloud** (Recommended for development)
   ```bash
   # Sign up at https://cloud.temporal.io
   # Get connection details and use in Python SDK
   ```

2. **Docker Compose** (Local development)
   ```bash
   git clone https://github.com/temporalio/docker-compose.git
   cd docker-compose
   docker-compose up
   ```

3. **Temporal CLI with Dev Server** (Simplest for prototyping)
   ```bash
   brew install temporal
   temporal server start-dev
   ```

### Sprint-6 Production Deployment
- Full Temporal HA deployment with external Postgres
- Proper schema migration and initialization
- Integration with Vault for credentials (Sprint-6 security hardening)
- Helm chart configuration will be revisited with more time

### Next Steps
1. Use Temporal dev server for Sprint-5 workflow development
2. Focus on Python SDK integration in orchestrator service
3. Build KAMACHIQ workflows with local Temporal instance
4. Plan proper production deployment for Sprint-6

**Squad:** Policy & Orchestration (Ada - Lead)  
**Alternative Approved By:** Engineering Leadership  
**Timeline Impact:** None - development continues with local setup
