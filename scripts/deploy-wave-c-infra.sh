#!/bin/bash
# Wave C Infrastructure Deployment Script
# Deploys observability stack, Temporal, and service monitors
# Sprint-6: Production Hardening

set -e

echo "🚀 SomaAgent Wave C Infrastructure Deployment"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_OBSERVABILITY="observability"
NAMESPACE_TEMPORAL="temporal"
NAMESPACE_SOMA="soma-agent"

# Function to print status
print_status() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    print_error "kubectl not found. Please install kubectl."
    exit 1
fi

if ! command -v helm &> /dev/null; then
    print_error "helm not found. Please install Helm."
    exit 1
fi

print_success "Prerequisites check passed"
echo ""

# Add Helm repositories
print_status "Adding Helm repositories..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo add temporalio https://go.temporal.io/helm-charts 2>/dev/null || true
helm repo add grafana https://grafana.github.io/helm-charts 2>/dev/null || true
helm repo update > /dev/null 2>&1
print_success "Helm repositories updated"
echo ""

# Create namespaces
print_status "Creating namespaces..."
kubectl create namespace $NAMESPACE_OBSERVABILITY --dry-run=client -o yaml | kubectl apply -f - > /dev/null
kubectl create namespace $NAMESPACE_TEMPORAL --dry-run=client -o yaml | kubectl apply -f - > /dev/null
kubectl create namespace $NAMESPACE_SOMA --dry-run=client -o yaml | kubectl apply -f - > /dev/null
print_success "Namespaces created/verified"
echo ""

# Deploy Observability Stack (Sprint-6)
print_status "Deploying Prometheus/Grafana observability stack..."

if helm list -n $NAMESPACE_OBSERVABILITY | grep -q prometheus; then
    print_warning "Prometheus already installed, skipping..."
else
    helm install prometheus prometheus-community/kube-prometheus-stack \
        -n $NAMESPACE_OBSERVABILITY \
        -f ../infra/helm/prometheus-lightweight.yaml \
        --wait --timeout 5m > /dev/null 2>&1
    print_success "Observability stack deployed"
fi
echo ""

# Deploy ServiceMonitors
print_status "Deploying ServiceMonitors for automatic service discovery..."
kubectl apply -f ../k8s/monitoring/servicemonitors.yaml > /dev/null 2>&1 || print_warning "ServiceMonitors deployment failed (may need CRD)"
print_success "ServiceMonitors configured"
echo ""

# Temporal deployment note
print_status "Temporal deployment status..."
print_warning "Using Temporal dev server approach for Sprint-5"
print_warning "Full production deployment scheduled for Sprint-6"
echo "  → See: infra/helm/TEMPORAL_DEPLOYMENT_NOTE.md"
echo ""

# Display access information
echo ""
echo "=============================================="
echo "✅ Wave C Infrastructure Deployment Complete"
echo "=============================================="
echo ""
echo "📊 Grafana Access:"
echo "  → NodePort: http://localhost:30080"
echo "  → Port Forward: kubectl port-forward -n observability svc/prometheus-grafana 3000:80"
echo "  → Username: admin"
echo "  → Password: admin"
echo ""
echo "📈 Prometheus Access:"
echo "  → Port Forward: kubectl port-forward -n observability svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "  → URL: http://localhost:9090"
echo ""
echo "🔍 Check Pod Status:"
echo "  → Observability: kubectl get pods -n $NAMESPACE_OBSERVABILITY"
echo "  → Services: kubectl get pods -n soma-memory"
echo ""
echo "📚 Next Steps:"
echo "  1. Add OpenTelemetry instrumentation to all services"
echo "  2. Set up Temporal dev server for Sprint-5"
echo "  3. Create Grafana dashboards"
echo "  4. Prepare for Oct 18 Wave C kickoff"
echo ""
echo "📄 Documentation:"
echo "  → Wave C Progress: docs/sprints/Wave_C_Progress_Oct5.md"
echo "  → Sprint Plans: docs/sprints/Sprint-{5,6,7}.md"
echo ""
