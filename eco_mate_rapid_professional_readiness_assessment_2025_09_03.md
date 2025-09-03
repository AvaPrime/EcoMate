# EcoMate – Rapid Professional‑Readiness Assessment (2025‑09‑03)

This snapshot evaluates the public contents of the `main` branch as of **2025‑09‑03**, and derives a prioritized action plan to raise EcoMate from a well‑structured prototype to an enterprise‑grade, secure, and community‑ready platform.

---

## 1) What the repo already does well

| Area | Evidence |
|---|---|
| Clear product positioning | README provides concise overview and how‑to‑start |
| Documentation‑as‑code | MkDocs Material config + rich Markdown hierarchy |
| Modular AI services | FastAPI entry‑point with routers for proposals, catalog, compliance |
| Infrastructure as code | `docker-compose.yml` (quick‑start), Makefile for artifacts |
| License present | MIT LICENSE file (to be replaced with proprietary) |
| Contribution scaffolding | CONTRIBUTING.md + roadmap/implementation packs |

These fundamentals give EcoMate a solid starter‑kit feel.

---

## 2) Gaps vs. professional/enterprise standards

| Category | Missing / Weak Items | Why it matters |
|---|---|---|
| Security & Compliance | `SECURITY.md`; Dependabot; CodeQL/secret‑scanning; GDPR/privacy statement; environmental compliance notes | Prevents supply‑chain attacks; satisfies audits |
| Code Quality & CI | Lint/format (Black, Ruff, isort); pre‑commit; tests + coverage; mypy; static analysis | Blocks regressions; improves maintainability |
| CI/CD Pipelines | Service build/test/push workflows; branch protection; release automation | Reliable, repeatable deployments |
| Packaging/Artifacts | API Dockerfile; Helm chart; `pyproject.toml` | Containerization & versioning |
| Documentation | ADRs; exported OpenAPI + Postman; prod “Getting Started” | Faster onboarding; clarity |
| Governance & Community | Code of Conduct; maintainers/ownership; labels for first‑timers | Clear stewardship |
| Observability/Ops | Prometheus metrics; health checks; logging guide; K8s overlays | SRE‑grade operations |
| Legal/Business | Terms, Privacy, AI advisory disclaimer | Minimizes legal exposure |

---

## 3) Action Plan — Prioritized, copy‑paste ready

### Phase 1 (Weeks 1–2): Security & Quality foundations

1. **Security policy** — `SECURITY.md`
```md
# Security Policy

**Reporting a vulnerability**

Please disclose security issues privately by emailing security@ecomate.com. Include a clear description, steps to reproduce, and any proof‑of‑concept code.

We will acknowledge receipt within 48 h and aim to fix the issue within 14 days.
```

2. **Dependabot** — `.github/dependabot.yml`
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5
```

3. **CodeQL** — `.github/workflows/codeql.yml`
```yaml
name: CodeQL
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
permissions:
  actions: read
  contents: read
  security-events: write
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v2
        with: { languages: python }
      - uses: github/codeql-action/autobuild@v2
      - uses: github/codeql-action/analyze@v2
```

4. **Pre‑commit hooks** — `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks: [{ id: black }]
  - repo: https://github.com/pycqa/ruff
    rev: v0.5.0
    hooks: [{ id: ruff, args: ["--fix"] }]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks: [{ id: mypy }]
```

5. **CI (lint + tests)** — `.github/workflows/ci.yml`
```yaml
name: CI
on: [push, pull_request]
jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -U pip pre-commit pytest coverage
      - run: pre-commit run --all-files
      - run: pytest -q --maxfail=1 --disable-warnings --cov=.
```

6. **Minimal test** — `ecomate-ai/tests/test_basic.py`
```python
from fastapi.testclient import TestClient
from services.api.main import app

def test_health():
    client = TestClient(app)
    r = client.get("/openapi.json")
    assert r.status_code == 200
```

7. **Audit tooling** — `tools/audit_repo.py`, `tools/audit_report.sh`, `.github/workflows/audit.yml` (see Playbook for full code)

---

### Phase 2 (Weeks 3–5): Ops & Release automation

8. **API Dockerfile** — `ecomate-ai/Dockerfile`
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

9. **Prometheus metrics & health** — in `services/api/main.py`
```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

@app.get("/healthz")
async def health():
    return {"status": "ok"}
```

10. **OpenAPI export (artifact)** — add CI step to save `openapi.json`/`yaml` as build artifact.

11. **Helm chart (basic)** — `helm/ecomate/...` (use `helm create ecomate`, set image to GHCR)

12. **Build & push image** — `.github/workflows/build-images.yml`
```yaml
name: Build & Push API Image
on: [push]
jobs:
  api:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: ecomate-ai
          push: true
          tags: ghcr.io/avaprime/ecomate-api:latest
```

---

### Phase 3 (Weeks 6–8): Governance, Community & Business docs

13. **Code of Conduct** — `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1)

14. **Maintainers** — `MAINTAINERS.md`
```md
# Maintainers
- @AvaPrime (Lead)
- @AvaPrime/platform (Core)
```

15. **Terms, Privacy, AI advisory** — `TERMS.md`, `PRIVACY.md`

16. **ADRs** — `adr/001-use-temporal.md` … (Nygard template)

17. **Release drafting** — Release Drafter or `gh release create` with `CHANGELOG.md`

---

## 4) License change — Proprietary

1. **Replace MIT** with `LICENSE.md`:
```md
# EcoMate Proprietary License
Copyright (c) 2025 AvaPrime. All rights reserved.

This software and its source code (the “Software”) are proprietary to AvaPrime. Unauthorized copying, modification, distribution, or use is prohibited except as expressly permitted by a written agreement with AvaPrime. The Software is provided “AS IS.”
```
2. (Optional) Keep docs under MIT in `docs/LICENSE-docs.md`.
3. Consider making the repo **Private**. If Public, the code remains visible but use is contract‑restricted.

---

## 5) GitHub settings — About, protections, Pages

- **About**
  - Description: `EcoMate: Proposal, compliance, telemetry & digital‑twin platform`
  - Website: set to GitHub Pages site URL
  - Topics: `sustainability, telemetry, water-treatment, digital-twin, compliance, ai`
- **Branch protection**: require `CI`, `CodeQL`, `Audit`, and tests.
- **Pages**: enable via Actions; point README badge to site.

**CLI examples**
```bash
gh repo edit AvaPrime/EcoMate \
  --description "EcoMate: Proposal, compliance, telemetry & digital‑twin platform" \
  --homepage "https://avaprime.github.io/EcoMate/" \
  --add-topic sustainability --add-topic telemetry --add-topic water-treatment \
  --add-topic digital-twin --add-topic compliance --add-topic ai
```

---

## 6) Docsites — MkDocs → GitHub Pages

- Ensure `mkdocs.yml` and `docs/index.md` exist and link to the **Master Index**.
- Action to publish:
```yaml
name: Publish Docs
on:
  push: { branches: [ main ] }
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install mkdocs mkdocs-material
      - run: mkdocs build --strict
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
```
- Verify Pages: open the URL from repo **About** → should return 200.

**OpenWiki / GitHub Wiki**: enable in Settings, create `Home`, link from MkDocs.

---

## 7) Make services live — API, Temporal UI, MinIO Console

> Use GHCR + your chosen runtime (Railway/Fly/Render/AWS). Local dev via compose:

```yaml
auth: &auth
  MINIO_ROOT_USER: admin
  MINIO_ROOT_PASSWORD: change-me

services:
  api:
    build: { context: ecomate-ai, dockerfile: Dockerfile }
    ports: ["8080:8080"]
  temporal-ui:
    image: temporalio/ui:latest
    environment: { TEMPORAL_ADDRESS: temporal:7233 }
    ports: ["8081:8080"]
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment: *auth
    ports: ["9000:9000", "9001:9001"]
```

**Verification**
- API `/healthz` → 200; `/docs` renders
- Temporal UI loads at exposed host
- MinIO Console loads at `:9001` and login works

---

## 8) First release (v0.1.0)

```bash
git tag -a v0.1.0 -m "EcoMate v0.1.0: Phase 1 foundation"
git push origin v0.1.0

gh release create v0.1.0 \
  --title "EcoMate v0.1.0" \
  --notes "Phase 1: security + quality + docs + containerized API" \
  --generate-notes
```
Attach artifacts (e.g., sample proposal PDF) if available.

---

## 9) Success metrics (2‑month targets)

| Metric | Baseline | Target |
|---|---|---|
| Test coverage | ~0% | ≥ 80% |
| Security alerts | None | Dependabot + CodeQL enabled; no open critical CVEs |
| CI pass rate | n/a | 100% on every push |
| Time to PR merge | n/a | ≤ 48 h |
| Deployment reproducibility | Manual | CI builds/pushes image + Helm chart |
| Observability | None | Prometheus + Grafana dashboards |
| Docs completeness | Partial | ADRs present; OpenAPI published |

---

## 10) Issue seeds (copy‑paste to GitHub)

- `feat(security): add SECURITY.md and CodeQL workflow`
- `chore(deps): enable Dependabot for pip`
- `chore(ci): add lint+test pipeline with pre-commit`
- `test(api): add minimal health/openapi tests`
- `feat(build): Dockerfile for API and GHCR push workflow`
- `feat(ops): expose Prometheus metrics and /healthz`
- `docs(adr): record decision to adopt Temporal`
- `docs(legal): add TERMS.md and PRIVACY.md`
- `governance: add CODE_OF_CONDUCT.md and MAINTAINERS.md`

---

By executing this plan, EcoMate moves from solid architecture and documentation to **professional readiness**: governed, observable, automated, and release‑capable.

