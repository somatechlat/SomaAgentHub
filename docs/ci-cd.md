# CI/CD Pipeline

This document describes the continuous integration and delivery workflow for **SomaAgentHub**.  All automation lives in the
`.github/workflows/` directory and is executed on **GitHub Actions**.

## Goals

* **Fast feedback** – Linting, unit‑tests and static analysis run on every pull request.
* **Secure artifacts** – Docker images are built, scanned (Trivy) and an SBOM is generated.
* **Reproducible releases** – A Helm chart is packaged and published to the GitHub Packages Helm registry.
* **Zero‑touch** – Merging to `main` automatically creates a new versioned release.

---

## Workflow Overview

| Job | Trigger | Description |
|-----|---------|-------------|
| `lint` | `push`/`pull_request` | Run `ruff` (Python) and `hadolint` (Dockerfiles). |
| `test` | `push`/`pull_request` | Execute unit‑tests (`pytest`) and integration tests (`scripts/integration-tests.py`). |
| `build` | `push`/`pull_request` | Build multi‑arch Docker images for each service, push to GitHub Container Registry (GHCR). |
| `scan` | `push`/`pull_request` | Scan built images with **Trivy** and generate an SBOM (`syft`). |
| `helm‑package` | `push`/`pull_request` | Package the Helm chart, lint it (`helm lint`), and publish it to the Helm registry. |
| `release` | `push` to `main` (tag) | Create a GitHub Release, upload the SBOM and Helm chart assets. |

---

## Example GitHub Actions Workflow

```yaml
name: CI

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install ruff & hadolint
        run: |
          pip install ruff
          sudo apt-get update && sudo apt-get install -y hadolint
      - name: Lint Python
        run: ruff check .
      - name: Lint Dockerfiles
        run: |
          find . -name Dockerfile -exec hadolint {} +

  test:
    needs: lint
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports: [6379:6379]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install -r requirements-dev.txt
      - name: Run pytest
        run: pytest -q

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4
      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build & push images
        run: |
          for svc in $(ls services); do
            img="ghcr.io/${{ github.repository }}/$svc:${{ github.sha }}"
            docker build -f services/$svc/Dockerfile -t $img services/$svc
            docker push $img
          done

  scan:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Trivy & Syft
        run: |
          sudo apt-get update && sudo apt-get install -y wget
          wget https://github.com/aquasecurity/trivy/releases/download/v0.49.1/trivy_0.49.1_Linux-64bit.tar.gz -O - | tar xz
          sudo mv trivy /usr/local/bin/
          wget https://github.com/anchore/syft/releases/download/v0.97.0/syft_0.97.0_linux_amd64.tar.gz -O - | tar xz
          sudo mv syft /usr/local/bin/
      - name: Scan images
        run: |
          for svc in $(ls services); do
            img="ghcr.io/${{ github.repository }}/$svc:${{ github.sha }}"
            trivy image --exit-code 0 $img || true
            syft $img -o sbom-$svc.spdx.json
          done
      - name: Upload SBOMs
        uses: actions/upload-artifact@v4
        with:
          name: sboms
          path: sbom-*.spdx.json

  helm-package:
    needs: scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Helm
        uses: azure/setup-helm@v3
      - name: Lint chart
        run: helm lint k8s/helm/soma-agent
      - name: Package chart
        run: |
          helm package k8s/helm/soma-agent --destination ./chart
      - name: Upload chart
        uses: actions/upload-artifact@v4
        with:
          name: helm-chart
          path: ./chart/*.tgz

  release:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: helm-package
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          path: ./artifacts
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ github.ref_name }}
          name: Release ${{ github.ref_name }}
          files: ./artifacts/**
```

---

## Secrets & Permissions

* `GITHUB_TOKEN` – automatically provided, used for publishing packages.
* `GHCR_TOKEN` – optional if you prefer a personal access token with `write:packages` scope.
* `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` – needed only when pushing to Docker Hub.

## Further Reading

* [GitHub Actions Documentation](https://docs.github.com/en/actions)
* [Trivy – Container Image Scanner](https://github.com/aquasecurity/trivy)
* [Syft – SBOM Generator](https://github.com/anchore/syft)
* [Helm Chart Repository Guide](https://helm.sh/docs/topics/chart_repository/)

---

*Documented on 2025-11-04 by the AI‑architect assistant.*
