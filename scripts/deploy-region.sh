#!/usr/bin/env bash
set -euo pipefail

# Deploy SomaAgent to a specific AWS region
# Usage: ./deploy-region.sh [us-west-2|eu-west-1] [apply|plan|destroy]

REGION="${1:-us-west-2}"
ACTION="${2:-plan}"

echo "🚀 Deploying SomaAgent to $REGION..."

cd "infra/terraform/$REGION"

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init -upgrade

# Select or create workspace
WORKSPACE="${WORKSPACE:-production}"
terraform workspace select "$WORKSPACE" 2>/dev/null || terraform workspace new "$WORKSPACE"

# Run Terraform action
case "$ACTION" in
  plan)
    echo "📋 Planning deployment..."
    terraform plan -out=tfplan
    ;;
  
  apply)
    echo "🔨 Applying infrastructure..."
    terraform apply -auto-approve tfplan 2>/dev/null || terraform apply -auto-approve
    
    # Export outputs
    echo ""
    echo "📊 Deployment outputs:"
    terraform output
    
    # Save outputs for kubectl config
    CLUSTER_NAME=$(terraform output -raw cluster_name)
    CLUSTER_ENDPOINT=$(terraform output -raw cluster_endpoint)
    
    # Update kubeconfig
    echo ""
    echo "🔧 Updating kubeconfig..."
    aws eks update-kubeconfig \
      --region "$REGION" \
      --name "$CLUSTER_NAME" \
      --alias "$CLUSTER_NAME"
    
    echo "✅ Deployment complete!"
    echo ""
    echo "Next steps:"
    echo "  kubectl config use-context $CLUSTER_NAME"
    echo "  kubectl get nodes"
    ;;
  
  destroy)
    echo "⚠️  Destroying infrastructure in $REGION..."
    read -p "Are you sure? Type 'yes' to confirm: " confirm
    if [ "$confirm" = "yes" ]; then
      terraform destroy -auto-approve
      echo "✅ Infrastructure destroyed"
    else
      echo "❌ Aborted"
      exit 1
    fi
    ;;
  
  *)
    echo "❌ Unknown action: $ACTION"
    echo "Usage: $0 [us-west-2|eu-west-1] [apply|plan|destroy]"
    exit 1
    ;;
esac
