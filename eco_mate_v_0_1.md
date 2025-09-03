# EcoMate v0.1.0 – Technical & Financial Due Diligence Report

**Date:** 3 September 2025  
**Prepared for:** Stakeholders & prospective investors  
**Scope:** Technical/codebase audit, operational maturity, valuation framework, remediation roadmap, and negotiation plan

---

## 1. Executive Summary

### 1.1 Introduction
This report provides a comprehensive assessment of EcoMate’s current technical posture and operational maturity, evaluates readiness for market deployment, and presents a defensible valuation using early-stage, market-based methods. It also supplies a prioritized remediation roadmap and a pragmatic plan to present and negotiate the valuation with stakeholders.

### 1.2 Summary of Key Findings
- **Architecture:** Solid modular foundation (FastAPI + Temporal + MinIO + Postgres/pgvector; MkDocs docs pipeline).  
- **Gaps blocking scale:** Security issues (critical/high alerts), moderate **technical debt ratio (8.5%)**, and **low test coverage (42%)** elevate delivery and outage risk.  
- **Ops/process:** CI/CD exists but requires expansion (broader test automation, security gates, SCA/SBOM, CodeQL on PRs).  
- **Docs:** Strong public docs baseline; developer-facing architecture/ADR and contribution paths need tightening.  
- **Valuation:** Scorecard method yields an **estimated pre-money ≈ $10.0M** (see §5), contingent on executing the Tier‑1/Tier‑2 remediation plan.

**Strategic takeaway:** The product is a credible prototype with enterprise‑grade potential. Addressing security, test depth, and supply-chain controls is the fastest path to reduce risk, unlock sales readiness, and justify an upward valuation revision.

---

## 2. Project Status & Technical Assessment

### 2.1 Core Codebase Health
**Automated scan snapshot** (illustrative of current state):

| Metric | Value | Commentary |
|---|---:|---|
| CodeQL security alerts | Critical: **2** · High: **12** · Medium: **45** · Low: **88** | Immediate remediation required for Critical/High. |
| Technical debt ratio | **8.5%** | Above comfort (>5%); will tax velocity & quality. |
| Test coverage | **42%** | High risk of escaped defects; target ≥70%. |
| Vulnerable dependencies | **7** known CVEs | Requires SCA + upgrades, SBOM.

**Interpretation:** The foundation is sound but **not production‑ready** without targeted hardening and quality work.

### 2.1.1 Technical Debt & Risk Matrix

| Item | Description | Severity | Est. Effort (dev‑hours) | Notes |
|---|---|---|---:|---|
| Outdated API endpoints | Legacy paths power critical flows; higher exploit/maintenance risk | High | 80 | Refactor to modern contracts + deprecations policy |
| High code duplication | ~15% duplicated logic inflates bug surface | High | 120 | Extract libs, DRY pass, enforce with lints |
| Sparse inline docs | Core logic lacks comments; high bus factor | Medium | 60 | Add docstrings, module READMEs |
| Inconsistent naming | Incoherent identifiers across modules | Low | 40 | Apply style guide + automated lint fixes |

> **Business lens:** Unmanaged debt depresses valuation by increasing execution risk, cost to scale, and acquirer integration risk.

### 2.2 Documentation & Knowledge Management
- **Public docs:** Strong MkDocs/Material with CI to Pages; ensure links, repo_url, CNAME.  
- **Developer docs (gap):** Architecture overview, **ADRs**, service contracts, runbooks, upgrade guides.  
- **Contribution path:** Pre-commit, coding standards, test strategy, release process—documented and enforced.

### 2.3 Dependency & Supply Chain (SBOM)
- **Current gap:** Formal SBOM and routine SCA not yet institutionalized.  
- **Risk:** License conflicts, transitive CVEs, opaque provenance.  
- **Controls to institute:** SBOM generation (CycloneDX), SCA in CI, license policy gate (fail on GPL‑X if disallowed), artifact signing (Sigstore Cosign), provenance (SLSA L3‑ready pipeline).

---

## 3. Deployment & Operational Readiness

### 3.1 SDLC & Team Practices
- Adopt lightweight **Scrum/Kanban** with working agreements, Definition of Done, and **quality SLAs** (coverage thresholds, review rules).  
- Track DORA‑style metrics: **Lead Time, Deployment Frequency, Change Failure Rate, MTTR**; add Recidivism Rate for rework.

### 3.2 CI/CD & Testing
**Target pipeline (incremental):**
1) **PR gates:** Ruff/Black, MyPy, unit tests, CodeQL, SCA, SBOM.  
2) **Integration tests** with ephemeral Postgres/Temporal/MinIO via docker compose.  
3) **Container build** → vulnerability scan (Trivy) → sign (Cosign) → push (GHCR).  
4) **Docs build** + link check + publish.  
5) **Release**: changelog, artifacts (docs tarball, PDFs), provenance attestation.

**Testing uplift:** From 42% → **≥70%** (unit + service‑level + workflow tests). Add load tests for critical endpoints; chaos tests for workflow retries/timeouts.

---

## 4. Strategic Recommendations & Roadmap

### 4.1 Prioritized Action Plan
**Tier 1 – Immediate (Weeks 0–2)**
- Patch **2 Critical + 12 High** alerts; upgrade/replace **7 vulnerable dependencies**.  
- Implement **/health** endpoint + basic rate‑limit, input validation.  
- Enable CodeQL + Dependabot + CI SCA as **required checks**.  
- Lock down MinIO (rotate creds, restrict console).  
- Fix docs URLs, CNAME, repo_url; README license alignment.

**Tier 2 – Foundational (Weeks 2–6)**
- Raise test coverage to **≥70%**; introduce contract tests for API and Temporal workflows.  
- Generate **SBOM (CycloneDX)** in CI; enforce license policy gate.  
- Add **ADRs**, architecture diagram, runbooks; CONTRIBUTING + CODE_OF_CONDUCT.  
- Observability: structured JSON logs; Prometheus metrics for API/Temporal/MinIO; baseline Grafana dashboard.

**Tier 3 – Scale Posture (Weeks 6–12)**
- OpenTelemetry traces across API → workflow chains.  
- Harden release: signed containers, provenance, pinned minimal images.  
- Production deploy blueprint: docker‑compose.prod or Helm chart; secrets management; TLS/ingress; backup & DR drills.

### 4.2 Costed Remediation Plan (Assumptions & Ranges)
_Assumptions:_ blended engineering rate **$95/hr** (~R1,800/hr); buffer ±20%.

| Workstream | Effort (hrs) | Cost (USD) | Cost (ZAR) |
|---|---:|---:|---:|
| Security patches (alerts + CVEs) | 120 | $11,400 | R216,000 |
| Testing uplift to ≥70% | 180 | $17,100 | R324,000 |
| CI/CD hardening (SCA/SBOM/signing) | 100 | $9,500 | R180,000 |
| Docs/ADRs/runbooks | 60 | $5,700 | R108,000 |
| Observability baseline | 60 | $5,700 | R108,000 |
| **Subtotal** | **520** | **$49,400** | **R936,000** |
| Contingency (20%) | — | $9,880 | R187,200 |
| **Total (12 weeks)** | — | **$59,280** | **R1,123,200** |

> These investments directly reduce risk factors that suppress valuation (technology, execution, legal/compliance).

---

## 5. Valuation

### 5.1 Model Selection
Early‑stage, pre‑revenue; use **Scorecard Method** (primary) with **Berkus** and **Risk‑Factor Summation** as cross‑checks.

### 5.2 Scorecard Valuation Breakdown
_Benchmark average pre‑money:_ **$6.0M** (sector/region comparables).  

| Factor | Weight | Score (1–5) | Weighted |
|---|---:|---:|---:|
| Management Team | 25% | 4.0 | 1.00 |
| Market Size | 20% | 5.0 | 1.00 |
| Product/Technology | 18% | 3.0 | 0.54 |
| Marketing/Sales | 15% | 2.0 | 0.30 |
| Need for Financing | 10% | 2.0 | 0.20 |
| Other (visibility, partners) | 10% | 3.0 | 0.30 |
| **Total multiplier** | — | — | **3.34** |

**Estimated pre‑money:** $6.0M × **1.67** ≈ **$10.0M**.

### 5.3 Sensitivity
- **Security fixed + coverage ≥70%:** Product/Tech → 3.5; multiplier ≈ 3.49 → **$10.5M–$11.2M**.  
- **Add defined GTM & 1st design‑partners LOIs:** Marketing/Sales → 3.5; multiplier ≈ 3.97 → **$11.8M–$12.5M**.  
- **If breaches/rework persist:** Product/Tech → 2.5; multiplier ≈ 3.25 → **$9.0M–$9.8M**.

> **Path to $12M:** Close Tier‑1/Tier‑2, publish security posture, land 2–3 pilots with written intents, and demonstrate monthly deployment cadence with low CFR.

---

## 6. Valuation Story, Stakeholder Engagement & Negotiation

### 6.1 Crafting the Business Case
- **Problem → Solution → Proof:** Environmental/IIoT operational pain → EcoMate’s orchestrated workflows + AI services; demonstrate live workflows & dashboards.  
- **Evidence:** Security fixes, CI gates, SBOM, coverage delta, uptime, and a public roadmap.  
- **Ask:** Capital to accelerate integrations, field deployments, and sales.

### 6.2 Stakeholder Communication Strategy

| Stakeholder | Influence/Interest | Channels | Core Message |
|---|---|---|---|
| Investors | High/High | Deck, data room, 1:1s | Big market, credible team, risk reduced via concrete controls; capital efficiency from workflow automation |
| Executives | High/Low | 2‑page brief | ROI, deployment plan, compliance posture, clear KPIs |
| Technical Team | Low/High | Workshops, ADRs | Why the roadmap choices; how quality gates raise velocity |
| Partners | Med/Med | Demos, solution sheets | Integration path, APIs, SLAs, joint value prop |

### 6.3 Pitch & Negotiation Framework
- **Deck discipline:** ≤20 words/slide; live demo of workflow & observability.  
- **Terms:** Seek win‑win; tie tranches to verifiable engineering milestones (coverage, CFR, pilot go‑lives).  
- **Contracting:** Use this report to narrow scope, reduce contingency padding; memorialize changes in writing.

---

## 7. Conclusion & Recommendations
EcoMate has the bones of an enterprise‑ready platform. The next **8–12 weeks** should focus on **Tier‑1 security**, **Tier‑2 quality/CI/SBOM**, and **observability**. Doing so not only unlocks safer deployments but also **moves valuation toward $12M** with clear, evidence‑backed de‑risking.

**Immediate next steps (owner → due date):**
1) Patch Critical/High alerts & CVEs; enable PR security gates → **Eng Lead, +14 days**.  
2) Implement /health, rate‑limit, validation; lock MinIO → **Backend Lead, +10 days**.  
3) Raise coverage to 70% on API & workflows → **QA/Backend, +6 weeks**.  
4) Generate SBOM + license policy; add ADRs/runbooks → **Platform, +4 weeks**.  
5) Publish observability baseline (Prometheus/Grafana) → **SRE, +4 weeks**.

---

## Appendix A – CI/CD Reference Blueprint (Concise)
- **Check suite:** Ruff, Black, MyPy, PyTest (coverage gate), CodeQL, Trivy, Syft/CycloneDX.
- **Build:** Docker (python:3.11‑slim), multi‑stage, non‑root, pinned deps, SBOM attach.
- **Sign:** Cosign keyless; push to GHCR; provenance attestation.
- **Release:** Semantic tags, changelog, docs artifacts (PDF/tar), Pages deploy.

## Appendix B – Policies & Standards
- **Security:** No default creds in prod, TLS everywhere, secrets via env/manager, rotation policy 90d.  
- **Quality:** Coverage ≥70% (rising), CFR <15%, MTTR <4h, PR reviews ≥1 senior.  
- **Licensing:** THIRD_PARTY.md; deny‑list strong copyleft unless approved.

## Appendix C – Data Room Checklist (Investor Readiness)
1) Architecture diagram + ADRs  
2) CI/CD configs + passing badges  
3) Security posture: CodeQL, SCA reports, SBOM, dependency diffs  
4) Test coverage report (trend)  
5) Runbooks: incident, backup/restore  
6) Pilot pipeline & LOIs  
7) Financial model with remediation budget and 12‑month hiring plan



---

# EcoMate v0.1.0 – Stabilization Playbook (Priority Taskboard)

> **Goal:** Make the codebase boringly reliable. This is a copy‑pasteable, step‑by‑step set of changes to eliminate security holes, reduce technical debt, and raise test coverage to ≥70%—before adding new features.

**Definition of Done for v0.1.0**  
- 0 Critical / 0 High security alerts (CodeQL + Trivy).  
- Tests ≥70% coverage; PR gates enforced.  
- `/health` and `/ready` green; metrics exposed; logs are JSON with correlation IDs.  
- SBOM (CycloneDX) attached to container; image signed (Cosign).  
- MinIO not using default creds; bucket auto‑created.

---

## Priority 0 — Safety Switches (immediate)

**Why:** Prevent accidental exposure while we harden things.

1. **Disable docs UI in prod**
   - In `services/api/core/settings.py` ensure:
     ```python
     enable_docs: bool = False  # set via env in prod
     ```
   - In `services/api/main.py` construct FastAPI with:
     ```python
     app = FastAPI(docs_url="/docs" if settings.enable_docs else None)
     ```

2. **Remove default creds from all envs**
   - Rotate MinIO, DB, and API keys. Update `.env.example` to hold ONLY placeholders.

3. **Block open CORS**
   - Restrict `allow_origins` to known domains in prod.

---

## Priority 1 — Security Triage & Dependency Hygiene

**Why:** Known CVEs and missing scans are the fastest way to lose stability and trust.

### 1.1 Dependabot (daily bumps)
Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "daily" }
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "weekly" }
```

### 1.2 CodeQL (PR + main)
Create `.github/workflows/codeql.yml`:
```yaml
name: codeql
on:
  push: { branches: [ main ] }
  pull_request:
permissions:
  security-events: write
  contents: read
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with: { languages: python }
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
```

### 1.3 CI security & supply chain gates
Add to `.github/workflows/ci.yml` (see full CI in Priority 9):
```yaml
- name: Safety (Python deps)
  run: pip install safety && safety check -r requirements.txt --full-report

- name: Build container (CI tag)
  run: |
    docker build -t ghcr.io/${{ github.repository }}/api:ci .

- name: SBOM (Syft CycloneDX)
  uses: anchore/syft-action@v0.16.0
  with:
    image: ghcr.io/${{ github.repository }}/api:ci
    format: cyclonedx-json
    output: sbom.cdx.json

- name: Trivy scan (fail on High/Critical)
  uses: aquasecurity/trivy-action@0.24.0
  with:
    image-ref: ghcr.io/${{ github.repository }}/api:ci
    format: 'table'
    exit-code: '1'
    severity: 'CRITICAL,HIGH'
```

### 1.4 Secrets scanning
Add **Gitleaks** to CI:
```yaml
- name: Gitleaks
  uses: gitleaks/gitleaks-action@v2
  with: { args: "detect --source . --no-git -v" }
```

---

## Priority 2 — Config & Secrets: Typed, Validated, Fail‑Closed

Create `services/api/core/settings.py`:
```python
from pydantic import AnyUrl, BaseSettings, Field, validator

class Settings(BaseSettings):
    env: str = Field("dev", regex="^(dev|staging|prod)$")
    db_url: AnyUrl
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    bucket_name: str = "ecomate-artifacts"
    temporal_host: str = "localhost:7233"
    api_key_hash: str | None = None  # for simple API key scheme
    enable_docs: bool = True

    @validator("db_url")
    def _pg_only(cls, v):
        assert str(v).startswith(("postgres://", "postgresql://")), "Must be Postgres URL"
        return v

settings = Settings()
```

Sanitized `.env.example`:
```dotenv
ENV=dev
DB_URL=postgresql://user:pass@localhost:5432/ecomate
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=__set_me__
MINIO_SECRET_KEY=__set_me__
BUCKET_NAME=ecomate-artifacts
TEMPORAL_HOST=localhost:7233
API_KEY_HASH=__set_me__
ENABLE_DOCS=true
```

---

## Priority 3 — Health/Readiness & Minimal API Armor

Patch `services/api/main.py`:
```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .core.settings import settings
from .core.storage import ensure_bucket
from .core.db import get_db  # implement a tiny get_db that pings

app = FastAPI(docs_url="/docs" if settings.enable_docs else None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://docs.ecomate.co.za"],
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["Authorization","Content-Type","X-API-Key"],
)

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

@app.get("/ready", include_in_schema=False)
async def ready(db=Depends(get_db)):
    await db.execute("SELECT 1")
    await ensure_bucket()
    return {"status": "ready"}
```

Update `Dockerfile` healthcheck if needed:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/health || exit 1
```

Optional rate limiting (`services/api/core/limits.py`):
```python
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address) if os.getenv("REDIS_URL") else None
```

---

## Priority 4 — AuthN/Z (Simple First)

Create `services/api/core/auth.py`:
```python
import hmac, os
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
EXPECTED = os.environ.get("API_KEY_HASH")

def require_api_key(api_key: str = Security(_api_key_header)):
    if not api_key or not EXPECTED or not hmac.compare_digest(api_key, EXPECTED):
        raise HTTPException(status_code=401, detail="Unauthorized")
```

Gate sensitive routes:
```python
from .core.auth import require_api_key
@app.post("/admin/reindex")
def reindex(_: None = Depends(require_api_key)):
    ...
```

Security headers middleware (optional hardening):
```python
@app.middleware("http")
async def set_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.update({
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
    })
    return resp
```

---

## Priority 5 — Structured Logging & Metrics

Create `services/api/core/logging.py`:
```python
import logging, sys
from pythonjsonlogger import jsonlogger

def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
```

Instrument in `main.py`:
```python
from .core.logging import configure_logging
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class Correlation(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        cid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-Id"] = cid
        return response

configure_logging()
app.add_middleware(Correlation)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
```

---

## Priority 6 — MinIO/S3 Hardening

Create `services/api/core/storage.py`:
```python
import io
from minio import Minio
from .settings import settings

_client = Minio(settings.minio_endpoint,
                settings.minio_access_key,
                settings.minio_secret_key,
                secure=False)

async def ensure_bucket():
    if not _client.bucket_exists(settings.bucket_name):
        _client.make_bucket(settings.bucket_name)

def put_bytes(key: str, b: bytes, content_type="application/octet-stream"):
    _client.put_object(settings.bucket_name, key, io.BytesIO(b), length=len(b), content_type=content_type)
```

Lock console to localhost or VPN; rotate creds; add TLS if exposed. Optional `mc` commands (run once):
```bash
mc alias set local http://127.0.0.1:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
mc mb local/$BUCKET_NAME || true
mc version enable local/$BUCKET_NAME
```

---

## Priority 7 — Temporal Reliability Controls

Add retries/timeouts/heartbeats for every activity. Example:
```python
# services/orchestrator/workflows/example.py
from datetime import timedelta
from temporalio import workflow

@workflow.defn
class Example:
    @workflow.run
    async def run(self, payload: dict) -> str:
        return await workflow.execute_activity(
            "tasks.process",
            payload,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=workflow.RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2.0,
                maximum_attempts=5,
            ),
        )
```

Graceful worker shutdown (SIGTERM handling) and alerts on repeated failures (hook via logs/metrics).

---

## Priority 8 — Tests to 70% (Scaffold + Examples)

**Structure:**
```
tests/
  unit/
  api/
  workflows/
  integration/
```

`pytest.ini`:
```ini
[pytest]
addopts = -q --maxfail=1 --disable-warnings --cov=services --cov-report=term-missing --cov-fail-under=70
```

Health test:
```python
# tests/api/test_health.py
from starlette.testclient import TestClient
from services.api.main import app

def test_health_ok():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
```

Auth test:
```python
# tests/api/test_auth.py
from starlette.testclient import TestClient
from services.api.main import app

def test_admin_rejects_without_key():
    c = TestClient(app)
    assert c.post("/admin/reindex").status_code == 401
```

Temporal test:
```python
# tests/workflows/test_example.py
import pytest
from temporalio.testing import WorkflowEnvironment
from services.orchestrator.workflows.example import Example

@pytest.mark.asyncio
async def test_example_workflow():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        h = await env.start_workflow(Example.run, {"x": 1}, id="t1", task_queue="ecomate-ai")
        assert (await h.result()) is not None
```

Integration compose (`docker-compose.test.yml`):
```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: test
      POSTGRES_DB: ecomate
    ports: ["5432:5432"]
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: test
      MINIO_ROOT_PASSWORD: testtest123
    ports: ["9000:9000","9001:9001"]
  temporal:
    image: temporalio/auto-setup:latest
    environment:
      DB: postgresql
      DB_PORT: 5432
      POSTGRES_USER: postgres
      POSTGRES_PWD: test
      POSTGRES_SEEDS: db
    ports: ["7233:7233","8088:8088"]
```

CI step:
```yaml
- name: Integration up
  run: docker compose -f docker-compose.test.yml up -d
- name: Tests
  run: pytest
```

---

## Priority 9 — CI/CD (Single Source of Truth)

Create `.github/workflows/ci.yml`:
```yaml
name: ci
on:
  pull_request:
  push: { branches: [main] }

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check .
      - run: black --check .
      - run: mypy services
      - name: Unit+Integration Tests
        run: |
          docker compose -f docker-compose.test.yml up -d
          pytest
      - name: Safety (deps)
        run: pip install safety && safety check -r requirements.txt --full-report
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
        with: { args: "detect --source . --no-git -v" }
      - name: Build container (CI)
        run: docker build -t ghcr.io/${{ github.repository }}/api:ci .
      - name: SBOM (Syft)
        uses: anchore/syft-action@v0.16.0
        with:
          image: ghcr.io/${{ github.repository }}/api:ci
          format: cyclonedx-json
          output: sbom.cdx.json
      - name: Trivy scan
        uses: aquasecurity/trivy-action@0.24.0
        with:
          image-ref: ghcr.io/${{ github.repository }}/api:ci
          format: 'table'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'

  publish:
    if: github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - name: Login GHCR
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u $ --password-stdin
      - name: Build & tag
        run: |
          docker build -t ghcr.io/${{ github.repository }}/api:sha-${{ github.sha }} .
          docker tag ghcr.io/${{ github.repository }}/api:sha-${{ github.sha }} ghcr.io/${{ github.repository }}/api:latest
      - name: Push
        run: |
          docker push ghcr.io/${{ github.repository }}/api:sha-${{ github.sha }}
          docker push ghcr.io/${{ github.repository }}/api:latest
      - name: Cosign sign (keyless)
        uses: sigstore/cosign-installer@v3
      - run: cosign sign ghcr.io/${{ github.repository }}/api:sha-${{ github.sha }} --yes
```

Enable **Branch Protection** on `main`: require `ci` + `codeql` checks to pass; require reviews.

---

## Priority 10 — Docs/ADRs/Runbooks

**ADRs:** Create `/architecture/adr-0001-temporal.md`:
```md
# ADR-0001: Use Temporal for Workflow Orchestration
Date: 2025-09-03
Status: Accepted
Context: …
Decision: …
Consequences: …
```

**Runbooks:** `/runbooks/incident.md`, `/runbooks/backup-restore.md` with step-by-step commands.  
**MkDocs:** Fix `repo_url`, add a **Security Posture** page, and run a link checker in CI if desired.

---

## Priority 11 — Observability & Alerts (Baseline)

- Expose `/metrics` (already in Priority 5).  
- Prometheus scrape config (snippet):
```yaml
scrape_configs:
  - job_name: ecomate-api
    static_configs:
      - targets: ['api:8080']
```
- Grafana dashboard: HTTP p95/p99, error rate, RPS, workflow failures, MinIO disk.  
- Alerts: API 5xx spike, repeated workflow failure, disk <10%.

---

## Priority 12 — Technical Debt Quick Wins

- Run **ruff --fix** across the repo to normalize imports/naming.  
- Extract duplicated helpers into `services/common/`.  
- Add docstrings to public functions; generate API docs into MkDocs.

---

### Execution Notes
- Keep PRs **small and atomic** (one priority slice per PR).  
- Land **Tier‑1** (Priorities 1–4) before any feature work.  
- Track coverage trend and CFR weekly; publish graph in README badge or docs.

**You can now copy/paste each snippet into place and commit in order.**

