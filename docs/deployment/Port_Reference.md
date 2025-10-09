# Port Reference

Last Updated: October 9, 2025

| Service          | Container Port | Service Type | Cluster Port | Notes                     |
|------------------|----------------|--------------|--------------|---------------------------|
| gateway-api      | 8080           | NodePort     | 8080/30080   | 30080 on node by default  |
| slm-service      | 1001           | ClusterIP    | 1001         | Internal-only by default  |
| orchestrator     | 1004           | ClusterIP    | 1004         | Optional in local         |
| identity-service | 8000           | ClusterIP    | 8000         | Token issuance            |
| policy-engine    | 8000           | ClusterIP    | 8000         | OPA-backed decisions      |

Port-forward examples:

```bash
kubectl -n soma-agent-hub port-forward svc/gateway-api 8080:8080
kubectl -n soma-agent-hub port-forward svc/slm-service 11001:1001
```
