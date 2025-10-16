#!/bin/bash
#
# This script provides an intelligent, idempotent way to manage the local development cluster.
#
# Logic:
# 1. Check if the cluster exists.
# 2. If it exists, check its health.
#    - If healthy, do nothing.
#    - If unhealthy, prompt the user to recreate it.
# 3. If it does not exist, create it.
#

set -e

CLUSTER_NAME="soma-agent-hub"
NAMESPACE="soma-agent-hub"

# --- Helper Functions ---
info() {
    echo "INFO: $1"
}

check_cluster_exists() {
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        return 0 # Cluster exists
    else
        return 1 # Cluster does not exist
    fi
}

check_cluster_health() {
    info "Checking cluster health..."
    # Get all pods in the namespace, filter for non-running pods
    NON_RUNNING_PODS=$(kubectl get pods -n ${NAMESPACE} --no-headers 2>/dev/null | awk '$3 != "Running" && $3 != "Completed" {print $1}' | wc -l)

    if [ "${NON_RUNNING_PODS}" -gt 0 ]; then
        info "Found ${NON_RUNNING_PODS} pods not in a 'Running' state."
        return 1 # Unhealthy
    else
        info "All pods are running correctly."
        return 0 # Healthy
    fi
}

# --- Main Logic ---

if check_cluster_exists; then
    info "Cluster '${CLUSTER_NAME}' already exists."
    if check_cluster_health; then
        info "Cluster is healthy. No action needed."
        exit 0
    else
        echo "WARNING: Cluster is in an unhealthy state."
        read -p "Do you want to destroy and recreate the cluster? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            info "User approved. Proceeding with cluster recreation."
            make stop-cluster
            make start-cluster
        else
            info "User declined. Leaving cluster in its current state for inspection."
            exit 1
        fi
    fi
else
    info "Cluster '${CLUSTER_NAME}' does not exist. Creating it now."
    make start-cluster
fi

info "Cluster management script finished successfully."
