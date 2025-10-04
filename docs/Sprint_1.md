⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Sprint 1 – Kubernetes Ready & Core Services

**Duration:** 2 weeks

## Goal
Stabilize the Kubernetes deployment, replace placeholder images with real service images, add health‑check probes, and document the deployment process. This will give the team a reliable foundation for further development and CI integration.

## Deliverables
1. **Stable Kind cluster** – the integration script (`run_full_k8s_test.sh`) runs cleanly on a fresh cluster multiple times.
2. **Real Docker images** for all micro‑services pushed to a registry and referenced in `k8s/helm/soma-agent/values.yaml`.
3. **Liveness & readiness probes** added to every Deployment.
4. **Updated documentation** (`docs/Kubernetes-Setup.md`) covering:
   - How to build and push images.
   - How to deploy the chart with custom images.
   - Quick‑start script for developers.
5. **CI pipeline enhancements** – lint, template, and a Helm‑test smoke‑check that fails the PR if any pod stays non‑Ready after 5 min.

## Tasks & Owners
| # | Task | Owner | Acceptance Criteria |
|---|------|-------|----------------------|
| 1 | Run the integration script repeatedly on a fresh Kind cluster to confirm stability. | DevOps | No pod remains Pending; script completes without errors.
| 2 | Build Docker images for each service (`jobs`, `slm-service`, `policy-engine`, `memory-gateway`, `orchestrator`, `settings-service`, `task-capsule-repo`). | Backend Lead | Images are tagged `soma-agent/<service>:<commit‑sha>` and pushed to the chosen registry.
| 3 | Update `values.yaml` with the real image references. | Backend Lead | Helm install uses the new images; `kubectl get pods` shows the correct images.
| 4 | Add `livenessProbe` and `readinessProbe` to each Deployment (use existing `/health` endpoints). | Backend Lead | Pods restart automatically when health checks fail; `kubectl describe pod` shows probes.
| 5 | Write a quick‑start script (`scripts/dev-deploy.sh`) that builds images, pushes them, and runs `helm upgrade --install`. | DevOps | One‑liner script that a developer can run to get the full stack locally.
| 6 | Expand `docs/Kubernetes-Setup.md` with sections on building images, custom values, and the quick‑start script. | Tech Writer | Documentation builds without errors; new sections are clear and tested.
| 7 | Extend CI (`.github/workflows/ci.yml`):
   - `helm lint` and `helm template`.
   - Run `helm test soma-agent` after install.
   - Fail if any pod is not Ready after 5 min.
| CI Engineer | CI passes on clean code and fails on broken Helm chart.
| 8 | Review & merge all changes; tag the commit as `sprint1‑complete`. | Project Lead | All tasks marked done, PR approved, tag created.

## Definition of Done (DoD)
- All services are running with real images on a Kind cluster.
- Health checks are configured and verified.
- Documentation reflects the current workflow.
- CI pipeline runs the new Helm‑test step and blocks PRs on failures.
- Sprint demo completed and stakeholder sign‑off obtained.

---
*This file lives in `docs/Sprint_1.md` and should be kept up‑to‑date as tasks progress.*