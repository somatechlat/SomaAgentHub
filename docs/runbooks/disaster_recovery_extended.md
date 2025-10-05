# Disaster Recovery Extended Runbook

## Overview
Comprehensive disaster recovery procedures for SomaGent platform across all failure scenarios.

## Recovery Time & Point Objectives

| Service Tier | RTO (Recovery Time) | RPO (Data Loss) | Backup Frequency |
|--------------|---------------------|-----------------|------------------|
| Critical (Gateway, DB) | 15 minutes | 5 minutes | Continuous |
| High (KAMACHIQ, MAO) | 1 hour | 15 minutes | Hourly |
| Medium (Tool Service) | 4 hours | 1 hour | 4x daily |
| Low (Marketplace) | 24 hours | 24 hours | Daily |

---

## Backup Strategy

### Database Backups

#### Automated Backups (RDS)
```bash
# Configure automated backups
aws rds modify-db-instance \
  --db-instance-identifier somagent-production-db \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"

# Enable point-in-time recovery
aws rds modify-db-instance \
  --db-instance-identifier somagent-production-db \
  --enable-cloudwatch-logs-exports '["postgresql"]'

# List available backups
aws rds describe-db-snapshots \
  --db-instance-identifier somagent-production-db \
  --query 'DBSnapshots[*].[DBSnapshotIdentifier,SnapshotCreateTime]'
```

#### Manual Snapshot
```bash
# Create snapshot before major changes
aws rds create-db-snapshot \
  --db-instance-identifier somagent-production-db \
  --db-snapshot-identifier somagent-prod-manual-$(date +%Y%m%d-%H%M%S)

# Wait for completion
aws rds wait db-snapshot-completed \
  --db-snapshot-identifier somagent-prod-manual-20240115-140000
```

#### Export to S3
```bash
# Continuous export for long-term retention
aws rds start-export-task \
  --export-task-identifier somagent-export-$(date +%Y%m%d) \
  --source-arn arn:aws:rds:us-east-1:123456789:snapshot:somagent-latest \
  --s3-bucket-name somagent-db-exports \
  --iam-role-arn arn:aws:iam::123456789:role/RDSExportRole \
  --kms-key-id arn:aws:kms:us-east-1:123456789:key/...
```

### Application Data Backups

#### Kubernetes State
```bash
# Backup etcd
ETCDCTL_API=3 etcdctl snapshot save snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Upload to S3
aws s3 cp snapshot.db s3://somagent-backups/kubernetes/snapshot-$(date +%Y%m%d).db
```

#### Vault Secrets
```bash
# Backup Vault data
vault operator raft snapshot save vault-snapshot.snap

# Encrypt and upload
openssl enc -aes-256-cbc -salt -in vault-snapshot.snap -out vault-snapshot.snap.enc \
  -pass pass:$VAULT_BACKUP_PASSWORD

aws s3 cp vault-snapshot.snap.enc s3://somagent-backups/vault/snapshot-$(date +%Y%m%d).snap.enc
```

#### Redis Backups
```bash
# Trigger manual save
redis-cli BGSAVE

# Wait for completion
redis-cli INFO persistence | grep rdb_bgsave_in_progress

# Copy RDS file to S3
aws s3 cp /var/lib/redis/dump.rdb s3://somagent-backups/redis/dump-$(date +%Y%m%d).rdb
```

### Backup Verification

#### Weekly Restore Test
```bash
#!/bin/bash
# weekly-restore-test.sh

# Restore to test environment
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier somagent-test-restore \
  --db-snapshot-identifier somagent-prod-latest

# Wait for availability
aws rds wait db-instance-available --db-instance-identifier somagent-test-restore

# Run validation queries
psql -h somagent-test-restore.xxx.rds.amazonaws.com -U somagent -d somagent <<EOF
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM workflows;
SELECT COUNT(*) FROM capsule_packages;
EOF

# Cleanup
aws rds delete-db-instance \
  --db-instance-identifier somagent-test-restore \
  --skip-final-snapshot
```

---

## Disaster Scenarios

### Scenario 1: Complete Region Failure (AWS us-east-1)

#### Detection
- All services in us-east-1 unreachable
- AWS Health Dashboard shows region outage
- Multi-region monitoring shows 100% failure

#### Recovery (Multi-Region Failover)

**Step 1: Promote Secondary Region (us-west-2)**
```bash
# Update DNS to point to us-west-2
aws route53 change-resource-record-sets --hosted-zone-id Z123456 --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.somagent.ai",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "Z789012",
        "DNSName": "somagent-us-west-2-alb.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }]
}'

# Promote read replica to primary
aws rds promote-read-replica \
  --db-instance-identifier somagent-us-west-2-db-replica \
  --backup-retention-period 30

# Scale up us-west-2 services
kubectl scale deployment/gateway-api --replicas=15 -n somagent-production --context=us-west-2
kubectl scale deployment/tool-service --replicas=20 -n somagent-production --context=us-west-2
kubectl scale deployment/kamachiq-service --replicas=10 -n somagent-production --context=us-west-2

# Verify services
kubectl get pods -n somagent-production --context=us-west-2
curl https://api.somagent.ai/health
```

**RTO:** 15 minutes  
**RPO:** 5 minutes (replication lag)

---

### Scenario 2: Database Corruption

#### Detection
- Database queries returning inconsistent data
- Application errors: "data integrity violation"
- Backup corruption detected in validation

#### Recovery (Point-in-Time Restore)

```bash
# Identify corruption time
# Assumption: Last known good state was 2024-01-15 10:00 UTC

# Restore to point-in-time
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier somagent-production-db \
  --target-db-instance-identifier somagent-production-db-pitr \
  --restore-time 2024-01-15T10:00:00Z \
  --db-instance-class db.r5.2xlarge

# Wait for restoration
aws rds wait db-instance-available \
  --db-instance-identifier somagent-production-db-pitr

# Validate data integrity
psql -h somagent-production-db-pitr.xxx.rds.amazonaws.com -U somagent -d somagent <<EOF
-- Check row counts
SELECT 'projects', COUNT(*) FROM projects
UNION ALL SELECT 'workflows', COUNT(*) FROM workflows
UNION ALL SELECT 'executions', COUNT(*) FROM executions;

-- Check for orphaned records
SELECT COUNT(*) FROM executions e 
LEFT JOIN workflows w ON e.workflow_id = w.id 
WHERE w.id IS NULL;
EOF

# If valid, switch application to new database
kubectl set env deployment/gateway-api \
  DATABASE_URL=postgresql://somagent:pwd@somagent-production-db-pitr:5432/somagent \
  -n somagent-production

# Verify application
curl https://api.somagent.ai/projects

# After 24-hour validation, rename instances
# Old: somagent-production-db → somagent-production-db-corrupted
# New: somagent-production-db-pitr → somagent-production-db
```

**RTO:** 2 hours  
**RPO:** Depends on restore time (up to 5 minutes)

---

### Scenario 3: Kubernetes Control Plane Failure

#### Detection
- kubectl commands fail
- Pods not scheduling
- HPA not scaling

#### Recovery (Rebuild Control Plane)

```bash
# AWS EKS: Control plane managed by AWS, auto-recovers
# Monitor recovery
aws eks describe-cluster --name somagent-production --query 'cluster.status'

# If prolonged outage, create new cluster
eksctl create cluster \
  --name somagent-production-dr \
  --region us-east-1 \
  --nodegroup-name compute \
  --node-type t3.xlarge \
  --nodes 10 \
  --nodes-min 3 \
  --nodes-max 30

# Restore from backup
# 1. Restore etcd snapshot
ETCDCTL_API=3 etcdctl snapshot restore snapshot.db

# 2. Redeploy applications
kubectl apply -f k8s/deployments/ --context=somagent-production-dr
kubectl apply -f k8s/services/ --context=somagent-production-dr
kubectl apply -f k8s/configmaps/ --context=somagent-production-dr

# 3. Update DNS
aws route53 change-resource-record-sets ... (point to new cluster ALB)
```

**RTO:** 1 hour  
**RPO:** 0 (stateless services)

---

### Scenario 4: Complete Data Center Loss

#### Detection
- All availability zones in region offline
- Physical disaster (fire, flood, earthquake)

#### Recovery (Cross-Region Failover)

```bash
# Automated failover via Route 53 health checks
# Manual verification and promotion

# 1. Verify secondary region health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-west-2:... \
  --region us-west-2

# 2. Promote database replica
aws rds promote-read-replica \
  --db-instance-identifier somagent-us-west-2-db \
  --region us-west-2

# 3. Update application config
kubectl set env deployment/gateway-api \
  DATABASE_URL=postgresql://...us-west-2.rds.amazonaws.com... \
  --context=us-west-2 \
  -n somagent-production

# 4. Scale up services (already done via autoscaling)

# 5. Verify full functionality
./scripts/smoke-tests.sh https://api-us-west-2.somagent.ai
```

**RTO:** 30 minutes  
**RPO:** 15 minutes (cross-region replication lag)

---

### Scenario 5: Ransomware / Security Breach

#### Detection
- Unusual database writes
- Encrypted file systems
- Unauthorized access logs

#### Recovery (Isolated Restore)

```bash
# 1. IMMEDIATELY isolate compromised systems
kubectl delete namespace somagent-production  # Nuclear option

# 2. Create isolated recovery environment
eksctl create cluster --name somagent-recovery-isolated ...

# Apply network policies (no external access)
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-egress
  namespace: somagent-recovery
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress: []  # Deny all outbound
EOF

# 3. Restore from clean backup (before breach)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier somagent-recovery-db \
  --db-snapshot-identifier somagent-prod-20240110-pre-breach

# 4. Deploy applications in recovery namespace
kubectl apply -f k8s/deployments/ -n somagent-recovery

# 5. Forensic analysis
# - Analyze breach timeline
# - Identify compromised credentials
# - Review audit logs

# 6. Remediation
# - Rotate ALL credentials (Vault, GitHub tokens, AWS keys)
# - Patch vulnerabilities
# - Restore clean data

# 7. Gradual restoration
# - After 72-hour validation, promote recovery to production
# - Update DNS to recovery environment
# - Monitor for 2 weeks before decommissioning old environment
```

**RTO:** 4-8 hours  
**RPO:** Depends on backup age (up to 24 hours to ensure clean data)

---

## Failover Testing

### Quarterly DR Drill Schedule

#### Q1: Database Failover
```bash
# Simulate primary database failure
./scripts/dr-drill-db-failover.sh

# Checklist:
# - [ ] Promote read replica within 5 minutes
# - [ ] Application switches to new primary
# - [ ] Zero data loss verified
# - [ ] No application errors
# - [ ] Rollback successful
```

#### Q2: Region Failover
```bash
# Simulate us-east-1 complete failure
./scripts/dr-drill-region-failover.sh

# Checklist:
# - [ ] DNS failover within 2 minutes (Route 53 health checks)
# - [ ] us-west-2 scales up automatically
# - [ ] RTO < 15 minutes
# - [ ] RPO < 5 minutes
# - [ ] All critical features functional
```

#### Q3: Data Restore
```bash
# Restore 7-day-old backup to test environment
./scripts/dr-drill-data-restore.sh

# Checklist:
# - [ ] Restore completes within 1 hour
# - [ ] Data integrity validated
# - [ ] Application connects successfully
# - [ ] Smoke tests pass
```

#### Q4: Full Infrastructure Rebuild
```bash
# Rebuild entire platform from backups
./scripts/dr-drill-full-rebuild.sh

# Checklist:
# - [ ] Kubernetes cluster created from scratch
# - [ ] Database restored from snapshot
# - [ ] Vault unsealed and secrets restored
# - [ ] All services deployed
# - [ ] DNS cutover
# - [ ] RTO < 4 hours
```

---

## Multi-Region Architecture

### Active-Active Setup

```
Primary Region (us-east-1):
- 3 AZs with full service deployment
- RDS Multi-AZ primary
- Redis cluster (3 shards, 2 replicas each)
- Route 53 weighted routing (70%)

Secondary Region (us-west-2):
- 3 AZs with full service deployment
- RDS read replica (promoted to primary on failover)
- Redis cluster (independent)
- Route 53 weighted routing (30%)

Global:
- Route 53 health checks every 30 seconds
- Automatic failover on health check failure (3 consecutive failures)
- CloudFront for static assets (multi-region origin)
```

### Cross-Region Replication

#### Database
```bash
# Create cross-region read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier somagent-us-west-2-replica \
  --source-db-instance-identifier somagent-us-east-1-db \
  --source-region us-east-1 \
  --region us-west-2 \
  --db-instance-class db.r5.2xlarge
```

#### S3 (File Storage)
```bash
# Enable cross-region replication
aws s3api put-bucket-replication --bucket somagent-uploads --replication-configuration '{
  "Role": "arn:aws:iam::123456789:role/S3ReplicationRole",
  "Rules": [{
    "Status": "Enabled",
    "Priority": 1,
    "Destination": {
      "Bucket": "arn:aws:s3:::somagent-uploads-us-west-2",
      "ReplicationTime": {
        "Status": "Enabled",
        "Time": {"Minutes": 15}
      }
    },
    "Filter": {}
  }]
}'
```

---

## Emergency Contacts

| Scenario | Primary Contact | Secondary Contact | Vendor Support |
|----------|----------------|-------------------|----------------|
| Database | DBA Team (@dba-oncall) | Platform Engineering | AWS Support (Premium) |
| Kubernetes | SRE Team (@sre-oncall) | DevOps | AWS EKS Support |
| Security Breach | Security Team (@security-oncall) | CTO | AWS Security Hub |
| Network | Network Engineering | AWS TAM | AWS Support |
| Application | Engineering Manager | Senior Engineers | N/A |

**AWS Support:** 1-877-742-2121 (Premium Support)  
**PagerDuty Escalation:** Automatically pages on-call chain

---

## Post-Recovery Checklist

After any disaster recovery:

- [ ] Complete post-incident review within 48 hours
- [ ] Update runbooks with lessons learned
- [ ] Test backup restoration process
- [ ] Verify monitoring and alerting
- [ ] Review and rotate credentials
- [ ] Update disaster recovery documentation
- [ ] Schedule follow-up DR drill within 90 days
- [ ] Communicate recovery metrics (RTO/RPO) to stakeholders
- [ ] Review insurance and SLA implications
- [ ] Update capacity planning based on failover load

---

## References
- [Incident Response](./incident_response.md)
- [AWS Disaster Recovery Whitepaper](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-workloads-on-aws.html)
- [Kubernetes Backup Best Practices](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/#backing-up-an-etcd-cluster)
- [RDS Backup Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html)
