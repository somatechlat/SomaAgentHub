# Volcano Sandbox Scripts

Utilities for provisioning and managing the local Volcano sandbox referenced in the integration roadmap.

- `bootstrap-kind.sh` – Creates a multi-node kind cluster and installs Volcano v1.9.0.
- `run-sample-session.sh` – Applies queue definitions, submits the sample session PodGroup/Job, and stores artifacts.
- `cleanup-sample.sh` – Removes sample resources (and optionally the interactive queue) after validation.

Prerequisites:
- `kind` v0.22+
- `helm` v3+
- Kubernetes CLI (`kubectl`) configured for local usage

Usage example:

```bash
# 1. Provision sandbox cluster + Volcano
chmod +x scripts/volcano/bootstrap-kind.sh
./scripts/volcano/bootstrap-kind.sh

# 2. Run the sample session workload and capture artifacts
chmod +x scripts/volcano/run-sample-session.sh
./scripts/volcano/run-sample-session.sh

# 3. Clean up resources (optional)
chmod +x scripts/volcano/cleanup-sample.sh
./scripts/volcano/cleanup-sample.sh
```
