# SomaAgentHub Backup and Recovery

**A guide to data protection, backup, and disaster recovery procedures.**

This document outlines the strategies and procedures for backing up critical data and recovering the SomaAgentHub platform in the event of a failure. It is essential for SREs, System Administrators, and Platform Engineers.

---

## 🎯 Data Protection Strategy

The platform's data is stored across several stateful components. A robust backup strategy must account for each one.

| Component | Data Type | Backup Method | Recovery Point Objective (RPO) | Recovery Time Objective (RTO) |
|---|---|---|---|---|
| **PostgreSQL** | Relational Data (users, policies) | Point-in-Time Recovery (PITR) | 5 minutes | 1 hour |
| **Qdrant** | Vector Embeddings (memory) | Volume Snapshots | 1 hour | 2 hours |
| **Temporal** | Workflow State | Database Backup (PostgreSQL) | 5 minutes | 1 hour |
| **Redis** | Cache & Session Data | Not backed up (transient) | N/A | N/A |
| **Kubernetes** | Configuration (secrets, configmaps)| GitOps (YAML manifests) | N/A | 30 minutes |

---

## 📦 Backup Procedures

### 1. PostgreSQL Database
We recommend using a robust backup tool like `pg_dump` or a managed database service's built-in backup capabilities (e.g., AWS RDS snapshots).

**Manual Backup using `pg_dump`:**
```bash
# 1. Get the PostgreSQL pod name
export PG_POD=$(kubectl get pods -n soma-agent-hub -l app=postgresql -o jsonpath='{.items[0].metadata.name}')

# 2. Execute pg_dump
kubectl exec -n soma-agent-hub $PG_POD -- \
  pg_dump -U <username> -d <database_name> > backup-$(date +%Y%m%d).sql
```

**Automated Backups:**
For production, use a Kubernetes CronJob to schedule daily backups and store them in a secure, remote location like an S3 bucket.

### 2. Qdrant Vector Database
Qdrant data is stored on a persistent volume. The most reliable backup method is to take periodic snapshots of this volume.

**Using a Volume Snapshot Controller:**
If your Kubernetes cluster has a CSI driver with snapshot capabilities:
```bash
# 1. Create a VolumeSnapshotClass if one doesn't exist
# 2. Create a VolumeSnapshot resource targeting the Qdrant PVC
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: qdrant-snapshot-$(date +%Y%m%d)
  namespace: soma-agent-hub
spec:
  volumeSnapshotClassName: <your-snapshot-class>
  source:
    persistentVolumeClaimName: <qdrant-pvc-name>
EOF
```

### 3. Kubernetes Configuration
All Kubernetes resources (Deployments, Services, ConfigMaps) are defined as code in this repository. The Git repository itself serves as the backup.

**Secrets should be managed separately** using a tool like HashiCorp Vault, AWS Secrets Manager, or Sealed Secrets, and backed up according to their own procedures.

---

## 🔄 Recovery Procedures (Disaster Recovery)

This section outlines the steps to recover the platform in a new, empty Kubernetes cluster.

### Step 1: Restore Infrastructure
- **Provision a new Kubernetes cluster** in the recovery region.
- **Set up prerequisites**: Ingress controller, storage classes, etc.

### Step 2: Restore Kubernetes Configuration
1.  **Clone the Git repository:**
    ```bash
    git clone https://github.com/somatechlat/somaAgentHub.git
    cd somaAgentHub
    ```
2.  **Restore Secrets:**
    Restore your Kubernetes secrets from your secrets management system.
    ```bash
    # Example for manual restoration
    kubectl apply -f /path/to/your/backed-up/secrets.yaml
    ```

### Step 3: Restore Stateful Data
1.  **Restore PostgreSQL:**
    Create a new PostgreSQL instance and restore the database from your SQL dump.
    ```bash
    # 1. Create a new PVC for PostgreSQL
    # 2. Start a temporary pod to run psql
    # 3. Restore the dump
    cat backup-YYYYMMDD.sql | kubectl exec -i -n soma-agent-hub <postgres-pod> -- psql -U <user> -d <db>
    ```

2.  **Restore Qdrant:**
    Create a new PersistentVolumeClaim from the volume snapshot you created earlier.
    ```yaml
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: qdrant-data-restored
      namespace: soma-agent-hub
    spec:
      storageClassName: <your-storage-class>
      dataSource:
        name: qdrant-snapshot-YYYYMMDD
        kind: VolumeSnapshot
        apiGroup: snapshot.storage.k8s.io
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 10Gi
    ```
    Update your Qdrant statefulset to use this restored PVC.

### Step 4: Deploy the Application
Once the data is restored, deploy the application using the Helm chart.

```bash
helm install soma-agent-hub k8s/helm/soma-agent/ \
  --namespace soma-agent-hub \
  --values /path/to/your/production-values.yaml
```

### Step 5: Verify the Recovery
- Run `kubectl get pods -n soma-agent-hub` to ensure all pods are healthy.
- Run the smoke tests (`make k8s-smoke`).
- Manually verify that user data and conversation history are present.

---

## 🧪 Disaster Recovery Testing

It is crucial to test your disaster recovery plan regularly.

**Recommended Testing Schedule:** Quarterly.

**Procedure:**
1.  Provision a temporary, isolated Kubernetes cluster.
2.  Follow the recovery procedures outlined above to restore a recent backup.
3.  Perform a thorough validation of the restored environment.
4.  Document any issues, update the recovery plan, and decommission the temporary cluster.

---

## 🔗 Related Documentation
- **[Deployment Guide](deployment.md)**: For initial deployment instructions.
- **[Operational Runbooks](runbooks/)**: For handling smaller, non-disaster incidents.
- **[System Architecture](architecture.md)**: To understand the stateful components.
