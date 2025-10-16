# Phase 2: Zero-Trust Network & Identity

**Status**: ✅ **Complete**  
**Date**: October 16, 2025  
**Components**: Istio Service Mesh + OPA/Gatekeeper + SPIRE Workload Identity

---

## Objective

Implement zero-trust architecture: automatic mTLS, policy-driven access control, cryptographic workload identity.

---

## 1. Istio Service Mesh

### Architecture

```
External Traffic
       ↓
  Ingress Gateway (port 80/443)
       ↓
┌─────────────────────────────────────┐
│    soma-agent-hub namespace         │
│    (istio-injection: enabled)       │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Gateway API (10000)        │   │
│  │  - Sidecar proxy (Envoy)    │   │
│  │  - mTLS enforced            │   │
│  └──────────┬──────────────────┘   │
│             │ (encrypted mTLS)      │
│             ↓                       │
│  ┌─────────────────────────────┐   │
│  │  Orchestrator (10001)       │   │
│  │  - Sidecar proxy (Envoy)    │   │
│  │  - mTLS enforced            │   │
│  └──────────┬──────────────────┘   │
│             │ (encrypted mTLS)      │
│             ↓                       │
│  ┌─────────────────────────────┐   │
│  │  Policy Engine (10020)      │   │
│  │  - Sidecar proxy (Envoy)    │   │
│  │  - mTLS enforced            │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘

All inter-service communication: mTLS encrypted
Certificates: auto-rotated by Istio
```

### Deployment

#### Prerequisites

```bash
# 1. Create Kubernetes cluster (Kind or managed)
kind create cluster --name soma-agent-hub --config k8s/kind-config.yaml

# 2. Verify cluster is ready
kubectl cluster-info
kubectl get nodes
```

#### Install Istio

```bash
# Download Istio 1.19+
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.19.0

# Add to PATH
export PATH=$PWD/bin:$PATH

# Install Istio using Helm (recommended for GitOps)
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

helm install istio-base istio/base \
  -n istio-system --create-namespace

helm install istiod istio/istiod \
  -n istio-system \
  -f ../../infra/helm/istio-values.yaml

helm install istio-ingressgateway istio/gateway \
  -n istio-system \
  --set service.type=LoadBalancer
```

#### Verify Istio Installation

```bash
# Check Istio system services
kubectl get pods -n istio-system
# Expected:
# istiod-xxxx                    1/1     Running
# istio-ingressgateway-xxxx      1/1     Running
# istio-egressgateway-xxxx       1/1     Running

# Check CRDs installed
kubectl get crd | grep istio
# Expected: virtualservices, destinationrules, peerauthentication, etc.

# Check Prometheus metrics
kubectl port-forward -n istio-system svc/istiod 8888:8888 &
curl http://localhost:8888/metrics | head -10
```

#### Deploy SomaAgentHub with Istio

```bash
# 1. Create namespaces with injection enabled
kubectl apply -f k8s/istio-namespaces.yaml

# 2. Apply mTLS policies (STRICT)
kubectl apply -f k8s/istio-peer-auth.yaml

# 3. Deploy services (auto-injected with Envoy sidecar)
kubectl apply -f k8s/soma-agent-hub-deployment.yaml

# 4. Create VirtualServices + DestinationRules
kubectl apply -f k8s/istio-virtual-services.yaml

# 5. Verify services have sidecars
kubectl get pods -n soma-agent-hub
# Expected: Each pod has 2/2 containers (app + envoy-sidecar)
```

### Verification

#### Test mTLS Enforcement

```bash
# 1. Verify certificates are automatically issued
kubectl get certs -n soma-agent-hub

# 2. Check certificate rotation (auto-renewed every 24h)
kubectl get secret -n soma-agent-hub | grep istio

# 3. Test service-to-service communication
# From gateway-api to orchestrator (should work)
kubectl exec -it <gateway-api-pod> -n soma-agent-hub -- \
  curl http://orchestrator:10001/ready

# 4. Test non-mTLS traffic is blocked
# From external (no sidecar) to service (should fail)
kubectl run test-pod --image=curlimages/curl --rm -it -- \
  curl http://gateway-api.soma-agent-hub:10000/ready
# Expected: Connection timeout (mTLS required)

# 5. Test with proper mTLS (from pod with sidecar)
kubectl exec -it <gateway-api-pod> -n soma-agent-hub -- \
  curl --cacert /etc/istio/certs/root-cert.pem \
       --cert /etc/istio/certs/cert-chain.pem \
       --key /etc/istio/certs/key.pem \
  https://orchestrator:10001/ready
# Expected: {"status": "ready"}
```

#### Monitor Traffic

```bash
# Install Kiali (Istio visualization)
kubectl apply -f k8s/kiali-deployment.yaml
kubectl port-forward -n istio-system svc/kiali 20000:20000 &
# Open http://localhost:20000
# Visualize service mesh topology + mTLS indicators

# Check traffic metrics in Prometheus
kubectl port-forward -n istio-system svc/prometheus 9090:9090 &
# Query: istio_requests_total (verify all services communication happening)
```

---

## 2. OPA/Gatekeeper Policy Enforcement

### Architecture

```
┌────────────────────────────────────────┐
│  Kubernetes API Server                 │
│  (admission webhook)                   │
└──────────────┬─────────────────────────┘
               │
               ↓
┌────────────────────────────────────────┐
│  Gatekeeper Controller                 │
│  (mutating + validating webhooks)      │
│                                        │
│  Policies (Rego):                      │
│  1. K8sRequiredRegistry                │
│     → Allow only official registries   │
│  2. K8sBlockPrivileged                 │
│     → Block privileged containers      │
│  3. K8sRequiredResources               │
│     → Enforce CPU/memory requests      │
│  4. K8sRequiredLabels                  │
│     → Require app/version labels       │
└────────────────────────────────────────┘
               ↓
          ACCEPT or DENY
          Pod creation
```

### Deployment

#### Install Gatekeeper

```bash
# Install Gatekeeper operator
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml

# Verify installation
kubectl get pods -n gatekeeper-system
# Expected: gatekeeper-audit-xxx, gatekeeper-controller-xxx

# Wait for webhooks to be ready
kubectl rollout status deployment/gatekeeper-controller -n gatekeeper-system --timeout=5m
```

#### Deploy Policies

```bash
# Apply all OPA/Rego policies
kubectl apply -f k8s/gatekeeper-policies.yaml

# Verify policies are installed
kubectl get constrainttemplate
# Expected: k8srequiredregistry, k8sblockprivileged, k8srequiredresources

kubectl get k8srequiredregistry
# Expected: soma-registry-policy ACTIVE
```

### Verification

#### Test Policy Violations

```bash
# 1. Test registry policy (should FAIL)
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: bad-registry
  namespace: soma-agent-hub
  labels:
    app: test
    version: v1
spec:
  containers:
    - name: app
      image: evil-registry.com/malware:latest
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
        limits:
          cpu: 500m
          memory: 512Mi
EOF
# Expected error: "Image 'evil-registry.com/malware:latest' from disallowed registry"

# 2. Test privileged policy (should FAIL)
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: bad-privileged
  namespace: soma-agent-hub
  labels:
    app: test
    version: v1
spec:
  containers:
    - name: app
      image: docker.io/alpine:latest
      securityContext:
        privileged: true
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
        limits:
          cpu: 500m
          memory: 512Mi
EOF
# Expected error: "Container 'app' is running in privileged mode"

# 3. Test resource limits policy (should FAIL)
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: bad-resources
  namespace: soma-agent-hub
  labels:
    app: test
    version: v1
spec:
  containers:
    - name: app
      image: docker.io/alpine:latest
      # Missing resources requests/limits
EOF
# Expected error: "Container 'app' missing resource requests"

# 4. Test valid pod (should SUCCEED)
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: good-pod
  namespace: soma-agent-hub
  labels:
    app: test
    version: v1
spec:
  containers:
    - name: app
      image: docker.io/alpine:latest
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
        limits:
          cpu: 500m
          memory: 512Mi
EOF
# Expected: Pod created successfully
```

#### View Policy Audit Logs

```bash
# Check which pods violated policies
kubectl logs -n gatekeeper-system -l gatekeeper.sh/system=yes -f

# Query violation metrics
kubectl port-forward -n gatekeeper-system svc/gatekeeper-webhook-service 8888:8888 &
curl http://localhost:8888/metrics | grep gatekeeper_violations

# Expected output shows count of policy violations per constraint
```

---

## 3. SPIRE Workload Identity

### Architecture

```
┌─────────────────────────────────────────────────┐
│  SPIRE Server (Control Plane)                   │
│  - PKI root of trust                            │
│  - Issues SVIDs (mTLS certificates)             │
│  - Database: PostgreSQL                         │
│  - Metrics: Prometheus (8888)                   │
│  - Port: 8081 (gRPC)                            │
└─────────┬───────────────────────────────────────┘
          │ (gRPC)
          ↓
┌─────────────────────────────────────────────────┐
│  SPIRE Agents (DaemonSet on every node)         │
│  - Attests pods via Kubernetes SA JWT           │
│  - Issues SVIDs to workloads                    │
│  - Stores certs in /run/spire/sockets/agent.sock│
│  - Auto-renews SVIDs before expiry              │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│  SomaAgentHub Services                          │
│  - Gateway API                                  │
│  - Orchestrator                                 │
│  - Identity Service                             │
│  - Policy Engine                                │
│                                                 │
│  Each service has SVID:                         │
│  spiffe://soma-agent-hub.local/ns/soma-../ \   │
│           ..../sa/gateway-api/uuid/...        │
│                                                 │
│  Automatic mTLS using SPIRE SVIDs               │
└─────────────────────────────────────────────────┘
```

### Deployment

#### Install SPIRE

```bash
# 1. Create SPIRE namespace + RBAC
kubectl apply -f k8s/spire-deployment.yaml

# 2. Wait for SPIRE server to be ready
kubectl rollout status statefulset/spire-server -n spire-system --timeout=5m

# 3. Wait for SPIRE agents to be ready
kubectl rollout status daemonset/spire-agent -n spire-system --timeout=5m

# 4. Verify SPIRE services are running
kubectl get pods -n spire-system
# Expected:
# spire-server-0           1/1     Running
# spire-agent-xxxxx        1/1     Running (one per node)
```

#### Register Workloads

```bash
# Using SPIRE CLI to register workloads
SPIRE_SERVER_POD=$(kubectl get pod -n spire-system -l app=spire-server -o jsonpath='{.items[0].metadata.name}')

# Register gateway-api workload
kubectl exec -it $SPIRE_SERVER_POD -n spire-system -- \
  /opt/spire/bin/spire-server entry create \
    -spiffeID spiffe://soma-agent-hub.local/ns/soma-agent-hub/sa/gateway-api \
    -parentID spiffe://soma-agent-hub.local/spire/agent/k8s_psat/soma-cluster/xxxxx \
    -selector k8s:sa:gateway-api \
    -selector k8s:ns:soma-agent-hub \
    -ttl 3600

# Register orchestrator workload
kubectl exec -it $SPIRE_SERVER_POD -n spire-system -- \
  /opt/spire/bin/spire-server entry create \
    -spiffeID spiffe://soma-agent-hub.local/ns/soma-agent-hub/sa/orchestrator \
    -parentID spiffe://soma-agent-hub.local/spire/agent/k8s_psat/soma-cluster/xxxxx \
    -selector k8s:sa:orchestrator \
    -selector k8s:ns:soma-agent-hub \
    -ttl 3600
```

#### Verify SPIRE Attestation

```bash
# 1. Check SPIRE agent is attesting nodes
kubectl logs -n spire-system -l app=spire-agent | grep "attestation"

# 2. Fetch SVID from pod
kubectl exec -it <gateway-api-pod> -n soma-agent-hub -- \
  cat /run/spire/sockets/agent.sock
# Expected: UNIX socket exists and is writable

# 3. Query SPIRE server for entries
kubectl exec -it $SPIRE_SERVER_POD -n spire-system -- \
  /opt/spire/bin/spire-server entry list
# Expected: List of registered SPIRE entries with SVID information

# 4. Verify certificate rotation
kubectl exec -it <gateway-api-pod> -n soma-agent-hub -- \
  /opt/spire/bin/spire-agent api fetch x509

# Expected output:
# Cert:     -----BEGIN CERTIFICATE-----
#           MIIDpDCCAo...
#           -----END CERTIFICATE-----
# Bundle:   -----BEGIN CERTIFICATE-----
#           ...root certificate...
#           -----END CERTIFICATE-----
```

---

## 4. Integration: Istio + OPA + SPIRE

### End-to-End Flow

```
1. Pod Creation Request
   ↓
2. Gatekeeper validates:
   ✓ Image from allowed registry
   ✓ Not privileged
   ✓ Has resource limits
   ✓ Has required labels
   ↓
3. Pod created in soma-agent-hub namespace
   ↓
4. Istio sidecar injector adds Envoy proxy
   ↓
5. SPIRE agent attests pod via K8s SA JWT
   ↓
6. SPIRE server issues SVID to pod
   ↓
7. Envoy proxy uses SVID for mTLS
   ↓
8. Service-to-service communication encrypted + authenticated
```

### Testing End-to-End

```bash
# 1. Deploy a test service
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-service
  namespace: soma-agent-hub
  labels:
    app: test
    version: v1
spec:
  serviceAccountName: test-service
  containers:
    - name: app
      image: docker.io/curlimages/curl:latest
      command: ["sleep", "1000"]
      resources:
        requests:
          cpu: 10m
          memory: 32Mi
        limits:
          cpu: 100m
          memory: 128Mi
EOF

# 2. Test mTLS communication to gateway-api
kubectl exec -it test-service -n soma-agent-hub -- \
  curl http://gateway-api:10000/ready
# Expected: {"status": "ready"}

# 3. Verify SPIRE issued certificate
kubectl exec -it test-service -n soma-agent-hub -- \
  ls -la /var/run/secrets/workload-spiffe/

# 4. Check Istio observability
kubectl logs test-service -n soma-agent-hub -c istio-proxy | grep TLS
# Expected: Logs showing TLS handshake

# 5. Query Kiali for traffic visualization
# http://localhost:20000/kiali
# Expected: Service graph with mTLS indicators
```

---

## 5. Verification Checklist

- ✅ Istio control plane running (istiod)
- ✅ Ingress gateway running
- ✅ All services have mTLS certificates
- ✅ OPA/Gatekeeper policies enforced
- ✅ Policy violations blocked
- ✅ SPIRE server running
- ✅ SPIRE agents running on all nodes
- ✅ Workloads issued SVIDs
- ✅ Service-to-service communication encrypted
- ✅ Metrics exported to Prometheus

---

## 6. Troubleshooting

### Istio Issues

```bash
# Check sidecar injection
kubectl get pods -n soma-agent-hub -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}{end}'
# Expected: Each pod should have 2 containers (app + istio-proxy)

# Check certificate expiry
kubectl get secret -n soma-agent-hub -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.data.tls\.crt}{"\n"}{end}' | \
  base64 -d | openssl x509 -noout -dates
```

### OPA Issues

```bash
# Check constraint templates
kubectl get constrainttemplate

# Check violation logs
kubectl logs -n gatekeeper-system -l gatekeeper.sh/system=yes

# Test policy manually
kubectl apply -f k8s/gatekeeper-policies.yaml --dry-run=server
```

### SPIRE Issues

```bash
# Check SPIRE agent logs
kubectl logs -n spire-system -l app=spire-agent

# Check SPIRE server logs
kubectl logs -n spire-system -l app=spire-server

# Verify SPIRE agent socket
kubectl exec -it <pod> -n soma-agent-hub -- \
  ls -la /run/spire/sockets/
```

---

## 7. Next Steps: Phase 3 (Governance)

After Phase 2:
- OpenFGA for fine-grained authorization
- Argo CD for GitOps deployments
- Kafka event pipeline for audit logs

---

**Status**: ✅ Phase 2 COMPLETE - Zero-Trust ready  
**Date**: October 16, 2025
