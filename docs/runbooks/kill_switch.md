# Kill Switch Runbook

Use this playbook to halt all new agent activity without tearing down infrastructure. Existing sessions may finish gracefully, but no new orchestration requests should be accepted.

## When to Trigger
- Suspected breach or compromise of credentials.
- Downstream dependency corruption (e.g., tool adapter release determined unsafe).
- Regulatory request to pause automation for a tenant or globally.

## Activation Steps
1. **Notify** stakeholders on incident channel and create an incident ticket.
2. **Flip gateway kill-switch**
   - Update deployment or config map with `SOMAGENT_GATEWAY_KILL_SWITCH_ENABLED=true`.
   - Redeploy the gateway (`kubectl rollout restart deployment/gateway-api`).
   - Verify `POST /v1/sessions` now returns HTTP 503 with `"Gateway kill-switch active"`.
   - Prometheus metric `gateway_moderation_decisions_total{outcome="kill_switch"}` should increment.
3. **Freeze tool executions (optional)**
   - Apply a NetworkPolicy denying egress from `tool-service` namespace.
   - Optionally scale the tool service to zero if adapters should be completely disabled.
4. **Invalidate credentials**
   - Call `identity-service` `PUT /v1/users/{id}` to set `active=false` for affected accounts.
   - Revoke existing JWTs by rotating the signing secret if compromise is suspected.
5. **Communicate** status updates every 15 minutes until resolved.

## Post-Activation Checks
- Confirm no new sessions appear in orchestrator logs.
- Verify `tool_adapter_executions_total` does not increase.
- Monitor moderation strike counters for unexpected spikes (should remain flat).

## Rollback
1. Confirm containment activities complete and obtain incident lead approval.
2. Re-enable gateway traffic by setting `SOMAGENT_GATEWAY_KILL_SWITCH_ENABLED=false` and redeploying.
3. Remove temporary NetworkPolicies or scale tool-service replicas back to normal.
4. Rotate any secrets that were exposed during the incident.
5. Document the timeline and lessons learned in the incident ticket.
