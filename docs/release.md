# Release Process

This document describes the standard **release workflow** for **SomaAgentHub**. It is used by the maintainers to create a new version, publish Docker images, and distribute the Helm chart.

---

## Prerequisites

* **GitHub permissions** – write access to the repository and the GitHub Packages container registry.
* **Local tools** – `git`, `gh` (GitHub CLI), `docker`, `helm`, and `poetry` (for Python services).
* **CI/CD pipeline** – the `ci-cd.yml` workflow must be passing on the `main` branch.

---

## Step‑by‑Step Release Procedure

1. **Create a release branch**
   ```bash
   git checkout -b release/vX.Y.Z
   ```
   Replace `X.Y.Z` with the target version (e.g., `1.2.0`).

2. **Update version numbers**
   * In `pyproject.toml` – bump the `version` field.
   * In each service’s `pyproject.toml` or `setup.cfg` (if applicable).
   * In the Helm chart (`k8s/helm/soma-agent/Chart.yaml`) – set `version` and `appVersion`.
   * Commit the changes:
   ```bash
   git commit -am "chore: bump version to vX.Y.Z"
   ```

3. **Run local tests** to ensure nothing broke:
   ```bash
   make test-all   # custom target that runs all service tests
   ```

4. **Push the release branch** and open a PR against `main`.
   ```bash
   git push origin release/vX.Y.Z
   gh pr create --base main --head release/vX.Y.Z --title "Release vX.Y.Z" --body "Release notes..."
   ```
   The CI workflow will run automatically. Ensure all jobs pass.

5. **Merge the PR** (use *Squash and merge* to keep a clean history).

6. **Create a Git tag** (this triggers the `deploy‑production` job in the CI/CD pipeline):
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

7. **Publish the Helm chart**
   The `ci‑cd.yml` workflow packages the chart and pushes it to the GitHub Packages Helm registry when a tag is created. Verify the chart is available:
   ```bash
   helm repo add soma-agent-hub https://ghcr.io/<owner>/somaAgentHub/helm-charts
   helm search repo soma-agent-hub
   ```

8. **Announce the release** – update the `CHANGELOG.md`, create a GitHub Release (the `gh release create` command can be used), and notify stakeholders.

---

## Release Checklist (for reviewers)

* [ ] Version numbers bumped in all relevant files.
* [ ] All CI jobs (test, lint, build, deploy‑staging) pass.
* [ ] Helm chart version matches the Git tag.
* [ ] `CHANGELOG.md` contains the new entries.
* [ ] Release notes drafted and attached to the GitHub Release.

---

*Last updated*: 2025‑11‑04
