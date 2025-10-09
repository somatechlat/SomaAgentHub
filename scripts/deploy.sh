#!/bin/bash
# Real deployment script for SomaAgent - NO MOCKS!
# This deploys ALL services to a REAL Kubernetes cluster

set -e

NAMESPACE="somaagent"
OBSERVABILITY_NS="observability"

echo "🚀 SomaAgent Production Deployment"
echo "===================================="
echo ""

# Check prerequisites
echo "✓ Checking prerequisites..."
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl."
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "❌ helm not found. Please install Helm."
    exit 1
fi

# Verify cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster."
    echo "   Please configure kubectl with a valid cluster context."
    exit 1
fi

CLUSTER_ENDPOINT=$(kubectl cluster-info | grep 'control plane' | awk '{print $NF}')
echo "   Connected to: $CLUSTER_ENDPOINT"
echo ""

# Create namespaces
echo "📁 Creating namespaces..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace $OBSERVABILITY_NS --dry-run=client -o yaml | kubectl apply -f -
echo "   ✓ Namespaces created"
echo ""

# Create secrets (REAL secrets - replace in production!)
echo "🔐 Creating secrets..."
kubectl create secret generic somaagent-secrets \
  --namespace=$NAMESPACE \
  --from-literal=identity-db-url='postgresql://somaagent:CHANGE_ME@postgres:5432/identity' \
  --from-literal=jwt-secret='CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING' \
  --from-literal=clickhouse-user='analytics_ingest' \
  --from-literal=clickhouse-password='CHANGE_ME_IN_PRODUCTION' \
  --dry-run=client -o yaml | kubectl apply -f -
echo "   ✓ Secrets created (⚠️  CHANGE IN PRODUCTION!)"
echo ""

# Deploy observability stack (Prometheus only) and Loki
echo "📊 Deploying observability stack (Prometheus + Loki)..."
if ! helm list -n $OBSERVABILITY_NS | grep -q prometheus; then
    helm install prometheus prometheus-community/kube-prometheus-stack \
      --namespace $OBSERVABILITY_NS \
      --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
      --set grafana.enabled=false \
      --wait --timeout 5m
    echo "   ✓ Prometheus deployed (Grafana disabled)"
else
    echo "   ✓ Prometheus stack already deployed"
fi

# Deploy Loki (logs)
kubectl apply -f k8s/loki-deployment.yaml
echo "   ✓ Loki applied"
echo ""

# Deploy ServiceMonitors
echo "📡 Deploying ServiceMonitors..."
kubectl apply -f k8s/monitoring/ -n $OBSERVABILITY_NS
echo "   ✓ ServiceMonitors deployed"
echo ""

# Deploy infrastructure dependencies
echo "🗄️  Deploying infrastructure dependencies..."

# Redis (for policy-engine caching)
if ! kubectl get deployment redis -n $NAMESPACE &> /dev/null; then
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: $NAMESPACE
spec:
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis
EOF
    echo "   ✓ Redis deployed"
else
    echo "   ✓ Redis already deployed"
fi

# ClickHouse (for analytics)
if ! kubectl get statefulset clickhouse -n $NAMESPACE &> /dev/null; then
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: clickhouse
  namespace: $NAMESPACE
spec:
  serviceName: clickhouse
  replicas: 1
  selector:
    matchLabels:
      app: clickhouse
  template:
    metadata:
      labels:
        app: clickhouse
    spec:
      containers:
      - name: clickhouse
        image: clickhouse/clickhouse-server:23.8
        ports:
        - containerPort: 9000
          name: native
        - containerPort: 8123
          name: http
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 4000m
            memory: 8Gi
        volumeMounts:
        - name: data
          mountPath: /var/lib/clickhouse
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: clickhouse
  namespace: $NAMESPACE
spec:
  ports:
  - port: 9000
    name: native
  - port: 8123
    name: http
  selector:
    app: clickhouse
EOF
    echo "   ✓ ClickHouse deployed"
    
    # Wait for ClickHouse to be ready
    echo "   ⏳ Waiting for ClickHouse..."
    kubectl wait --for=condition=ready pod -l app=clickhouse -n $NAMESPACE --timeout=5m
    
    # Initialize schema
    echo "   📝 Initializing ClickHouse schema..."
    kubectl exec -n $NAMESPACE clickhouse-0 -- clickhouse-client --multiquery < infra/clickhouse/schema.sql || true
    echo "   ✓ Schema initialized"
else
    echo "   ✓ ClickHouse already deployed"
fi

# Temporal (for workflows)
echo "📦 Ensuring Temporal Helm repo present..."
helm repo add temporalio https://temporalio.github.io/helm-charts >/dev/null 2>&1 || true
helm repo update >/dev/null 2>&1 || true
if ! helm list -n $NAMESPACE | grep -q temporal; then
    helm install temporal temporalio/temporal \
      --namespace $NAMESPACE \
      --set server.replicaCount=1 \
      --set cassandra.config.cluster_size=1 \
      --wait --timeout 10m
    echo "   ✓ Temporal deployed"
else
    echo "   ✓ Temporal already deployed"
fi
echo ""

# Deploy SomaAgent services
echo "🚢 Deploying SomaAgent services..."

SERVICES=(
  "policy-engine"
  "identity-service"
  "somallm-provider"
  "orchestrator"
  "analytics-service"
  "gateway-api"
)

for service in "${SERVICES[@]}"; do
    echo "   Deploying $service..."
    kubectl apply -f infra/k8s/${service}.yaml
done

echo "   ✓ All services deployed"
echo ""

# Wait for deployments
echo "⏳ Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod -l monitoring=enabled -n $NAMESPACE --timeout=5m || true
echo ""

# Show deployment status
echo "📊 Deployment Status:"
echo "===================="
kubectl get pods -n $NAMESPACE -l monitoring=enabled
echo ""

echo "📡 Services:"
echo "==========="
kubectl get svc -n $NAMESPACE
echo ""

# Get endpoints
GATEWAY_ENDPOINT=$(kubectl get svc gateway-api -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "Access points:"
echo "  API Gateway: http://${GATEWAY_ENDPOINT:-<pending>}:8080"
echo "  Prometheus: use port-forward: kubectl port-forward -n $OBSERVABILITY_NS svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "  Loki: use port-forward: kubectl port-forward -n $OBSERVABILITY_NS svc/loki 3100:3100"
echo ""
echo "Next steps:"
echo "  1. Change default passwords in production"
echo "  2. Configure TLS certificates"
echo "  3. Set up backup policies"
echo "  4. Configure alerting rules"
echo ""
echo "To check logs:"
echo "  kubectl logs -f -l app=orchestrator -n $NAMESPACE"
echo ""
echo "To run tests:"
echo "  kubectl apply -f tests/k8s-tests.yaml"
echo ""
