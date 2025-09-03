# EcoMate • Test Coverage Expansion Plan (Service‑by‑Service)

_Aim_: raise coverage from **3.36% → 40%** this sprint, then **65%**, then **≥85%** with CI enforcement. This plan gives you drop‑in fixtures, factories, and example tests for each service module (proposal, catalog, maintenance, compliance, telemetry, regulatory, geospatial, climate, iot).

> Assumptions: FastAPI app exposes routers for the listed services; you have a `.env.example`; database is Postgres; object storage is MinIO (S3‑compatible). Adjust endpoints if names differ.

---

## Sprint Targets & Order of Attack
1) **Golden‑path API integration tests** per service (happy paths)  → quick coverage wins.  
2) **Unit tests** for internal helpers (parsers, validators, normalizers).  
3) **Edge cases & failure paths** (invalid payloads, missing auth, timeouts).  
4) **Contract tests** (schemas/DTOs via Pydantic V2 `model_validate`).

**Coverage milestones**  
- **Sprint A (this doc)**: +~35–45 pp → files below.  
- **Sprint B**: add error‑path tests, repository/DAO tests, background tasks.  
- **Sprint C**: performance‑sensitive paths, retries, circuit‑breakers, and authz (OPA).

---

## Proposed Test Layout
```
.
├─ ecomate-ai/
│  └─ tests/
│     ├─ conftest.py
│     ├─ factories.py
│     ├─ utils/
│     │  ├─ s3_stub.py
│     │  └─ time.py
│     ├─ integration/
│     │  ├─ test_health.py
│     │  ├─ test_proposal_api.py
│     │  ├─ test_catalog_api.py
│     │  ├─ test_maintenance_api.py
│     │  ├─ test_compliance_api.py
│     │  ├─ test_telemetry_api.py
│     │  ├─ test_regulatory_api.py
│     │  ├─ test_geospatial_api.py
│     │  └─ test_climate_api.py
│     │  └─ test_iot_api.py
│     └─ unit/
│        ├─ test_parsers.py
│        ├─ test_normalizers.py
│        ├─ test_cost_model.py
│        ├─ test_bom_engine.py
│        └─ test_validators.py
└─ pytest.ini  (already present; see tweak below)
```

---

## Pytest/Coverage Settings (update)
In `pytest.ini` (keep your 85% gate, add pragmas for speed):
```ini
[pytest]
addopts = -q --maxfail=2 --disable-warnings --cov=ecomate_ai --cov-report=term-missing
filterwarnings =
    ignore::DeprecationWarning
markers =
    integration: marks tests as integration (deselect with '-m "not integration"')
    unit: marks tests as unit
```
> In CI, add `--cov-fail-under=40` for Sprint A, then raise to 65 and 85 in subsequent PRs.

---

## Fixtures & Test Utilities

### `tests/conftest.py`
Provides an app instance, async test client, isolated env, fake S3, and a temporary Postgres. If you can’t run Postgres locally, switch `TEST_USE_SQLITE=1` to use an in‑memory SQLite fallback (only for tests).
```python
# tests/conftest.py
import asyncio
import os
import tempfile
from contextlib import asynccontextmanager

import pytest
from httpx import AsyncClient

# Toggle to run tests with SQLite if Postgres is not available
USE_SQLITE = os.getenv("TEST_USE_SQLITE", "0") == "1"

# Ensure env is predictable for tests
os.environ.setdefault("ENV", "test")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "test")
os.environ.setdefault("MINIO_SECRET_KEY", "test")
os.environ.setdefault("S3_BUCKET", "ecomate-test")

if USE_SQLITE:
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
else:
    # Expect docker-compose to provide a test Postgres
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5433/ecomate_test",
    )

# Import after env is set so app picks it up correctly
from ecomate_ai.services.api.main import app as fastapi_app  # noqa: E402

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def app():
    # If your app has startup/shutdown events, ensure they run for tests
    yield fastapi_app

@pytest.fixture(scope="session")
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="function")
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d
```

### `tests/factories.py`
Minimal object/payload builders (expand as domain grows):
```python
# tests/factories.py
from datetime import datetime, timedelta
import random


def make_proposal_request():
    return {
        "site": {"lat": -34.036, "lon": 23.047, "altitude_m": 7},
        "needs": {"hot_water_daily_l": 200, "grid_connection": True},
        "constraints": {"budget_usd": 3500, "roof_area_m2": 20},
    }


def make_catalog_item():
    return {
        "sku": f"SKU-{random.randint(1000,9999)}",
        "name": "Solar Geyser 200L",
        "price": 899.99,
        "attributes": {"capacity_l": 200, "brand": "EcoMate"},
    }


def make_maintenance_job():
    next_week = datetime.utcnow() + timedelta(days=7)
    return {
        "asset_id": "asset-123",
        "task": "descale_heat_exchanger",
        "scheduled_at": next_week.isoformat() + "Z",
    }


def make_telemetry_batch(n=3):
    return {
        "device_id": "dev-42",
        "readings": [
            {"ts": (datetime.utcnow() - timedelta(seconds=i)).isoformat() + "Z", "temp_c": 55 + i}
            for i in range(n)
        ],
    }


def make_geojson_point():
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [23.047, -34.036]},
        "properties": {"name": "Site A"},
    }
```

### Optional: S3/MinIO Stub (if your code directly hits boto3)
```python
# tests/utils/s3_stub.py
class S3Stub:
    def __init__(self):
        self.store = {}

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.store[(Bucket, Key)] = Body

    def get_object(self, Bucket, Key):
        return {"Body": self.store[(Bucket, Key)]}
```
> If you use `aioboto3`/`boto3`, monkeypatch your S3 client creation to return `S3Stub` in tests.

---

## Integration Tests (per service)
_These are golden‑path examples. Adjust URLs/fields to match your routers._

### Health
```python
# tests/integration/test_health.py
import pytest

pytestmark = pytest.mark.integration

async def test_openapi_serves(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert "paths" in data
```

### Proposal
```python
# tests/integration/test_proposal_api.py
import pytest
from tests.factories import make_proposal_request

pytestmark = pytest.mark.integration

async def test_generate_proposal_happy_path(client):
    payload = make_proposal_request()
    r = await client.post("/proposal/generate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert {"bom", "estimate", "assumptions"} <= set(body.keys())

async def test_generate_proposal_validation_error(client):
    r = await client.post("/proposal/generate", json={"site": {}})
    assert r.status_code in (400, 422)
```

### Catalog
```python
# tests/integration/test_catalog_api.py
import pytest
from tests.factories import make_catalog_item

pytestmark = pytest.mark.integration

async def test_upsert_and_get_item(client):
    create = await client.post("/catalog/items", json=make_catalog_item())
    assert create.status_code in (200, 201)
    item = create.json()
    got = await client.get(f"/catalog/items/{item['sku']}")
    assert got.status_code == 200
    data = got.json()
    assert data["sku"] == item["sku"]
```

### Maintenance
```python
# tests/integration/test_maintenance_api.py
import pytest
from tests.factories import make_maintenance_job

pytestmark = pytest.mark.integration

async def test_schedule_maintenance(client):
    r = await client.post("/maintenance/schedule", json=make_maintenance_job())
    assert r.status_code in (200, 201)
    out = r.json()
    assert out.get("status") in {"scheduled", "queued"}
```

### Compliance
```python
# tests/integration/test_compliance_api.py
import pytest

pytestmark = pytest.mark.integration

async def test_run_compliance_check(client):
    payload = {
        "metrics": {"pressure_kpa": 400, "temp_c": 60},
        "standard": "SANS-10254",
    }
    r = await client.post("/compliance/check", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert {"compliant", "violations"} <= set(res.keys())
```

### Telemetry
```python
# tests/integration/test_telemetry_api.py
import pytest
from tests.factories import make_telemetry_batch

pytestmark = pytest.mark.integration

async def test_ingest_batch(client):
    r = await client.post("/telemetry/ingest", json=make_telemetry_batch())
    assert r.status_code in (200, 202)
```

### Regulatory
```python
# tests/integration/test_regulatory_api.py
import pytest

pytestmark = pytest.mark.integration

async def test_list_standards(client):
    r = await client.get("/regulatory/standards")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
```

### Geospatial
```python
# tests/integration/test_geospatial_api.py
import pytest
from tests.factories import make_geojson_point

pytestmark = pytest.mark.integration

async def test_validate_geojson_point(client):
    r = await client.post("/geospatial/validate-geojson", json=make_geojson_point())
    assert r.status_code == 200
    body = r.json()
    assert body.get("valid") is True
```

### Climate
```python
# tests/integration/test_climate_api.py
import pytest

pytestmark = pytest.mark.integration

async def test_get_forecast(client):
    r = await client.get("/climate/forecast?lat=-34.036&lon=23.047")
    assert r.status_code == 200
    data = r.json()
    assert {"daily", "source"} <= set(data.keys())
```

### IoT
```python
# tests/integration/test_iot_api.py
import pytest

pytestmark = pytest.mark.integration

async def test_send_device_command(client):
    cmd = {"command": "reboot", "args": {}}
    r = await client.post("/iot/devices/dev-42/command", json=cmd)
    assert r.status_code in (200, 202)
```

---

## Unit Tests (internal logic)
_Focus on parsers, normalizers, cost model, BOM engine, validators. These are fast and push coverage quickly._

### Parsers
```python
# tests/unit/test_parsers.py
from ecomate_ai.services.parsers.dispatcher import dispatch_parser

def test_dispatch_known_type():
    parser = dispatch_parser("shopify")
    assert callable(parser)

def test_dispatch_unknown_type_raises():
    import pytest
    with pytest.raises(KeyError):
        dispatch_parser("unknown")
```

### Normalizers
```python
# tests/unit/test_normalizers.py
from ecomate_ai.services.catalog.normalizers import normalize_price

def test_normalize_price_rounds_to_two_dp():
    assert normalize_price(12.3456) == 12.35
```

### Cost Model
```python
# tests/unit/test_cost_model.py
from ecomate_ai.services.proposal.cost_model import estimate_cost

def test_estimate_cost_basic():
    bom = [{"sku": "A", "qty": 2, "unit_price": 100.0}]
    out = estimate_cost(bom, labor_pct=0.2, overhead_pct=0.1)
    assert out["subtotal"] == 200.0
    assert 0 < out["total"] >= 200.0
```

### BOM Engine
```python
# tests/unit/test_bom_engine.py
from ecomate_ai.services.proposal.bom_engine import select_bom

def test_select_bom_200l_basic_case():
    spec = {"hot_water_daily_l": 200, "grid_connection": True}
    bom = select_bom(spec)
    assert isinstance(bom, list) and len(bom) > 0
```

### Validators (Pydantic V2)
```python
# tests/unit/test_validators.py
from ecomate_ai.domain.models import SiteSpec

def test_site_spec_validates_lat_lon():
    s = SiteSpec(lat=-34.036, lon=23.047, altitude_m=5)
    assert s.lat < 0 and s.lon > 0
```

---

## Makefile & Docker Compose (Testing Targets)
Add convenience targets:
```makefile
.PHONY: test test-sqlite test-fast

test:
	docker compose -f docker-compose.yml up -d db minio
	pytest -m "not slow" --cov=ecomate_ai --cov-fail-under=40

test-sqlite:
	TEST_USE_SQLITE=1 pytest --cov=ecomate_ai --cov-fail-under=40

test-fast:
	pytest -q -k unit
```
> Ensure your `docker-compose.yml` exposes Postgres on `5433` for tests or use a separate service `db_test`.

---

## CI Gate (GitHub Actions Snippet)
```yaml
# .github/workflows/test.yml
name: test
on: [push, pull_request]
jobs:
  unit-integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_USER: postgres
          POSTGRES_DB: ecomate_test
        ports: ["5433:5432"]
        options: >-
          --health-cmd="pg_isready -U postgres" --health-interval=10s --health-timeout=5s --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-dev.txt || true
      - run: pytest --cov=ecomate_ai --cov-report=term-missing --cov-fail-under=40
```

---

## API Documentation Alignment (fast follow)
- Add `docs/api/routers.md` that enumerates each router, its prefix, and key endpoints.
- Export OpenAPI: `curl http://localhost:8000/openapi.json > docs/api/openapi.json` and serve via MkDocs.
- Add a test that asserts critical paths exist in the OpenAPI (guards against doc drift).
```python
# tests/integration/test_openapi_contract.py
import pytest

pytestmark = pytest.mark.integration

CRITICAL_PATHS = [
    "/proposal/generate",
    "/catalog/items",
    "/maintenance/schedule",
]

async def test_openapi_contains_critical_paths(client):
    data = (await client.get("/openapi.json")).json()
    paths = set(data.get("paths", {}).keys())
    for p in CRITICAL_PATHS:
        assert p in paths, f"OpenAPI missing {p}"
```

---

## Rollout Plan (Issue Checklist)
- [ ] Land `tests/` structure and fixtures in `main` behind `TEST_USE_SQLITE` fallback.
- [ ] Implement/confirm endpoints to match or update tests accordingly.
- [ ] Sprint A PRs (by service):
  - [ ] Proposal API golden path + unit tests for cost model & BOM engine.
  - [ ] Catalog API golden path + unit tests for normalizers.
  - [ ] Compliance API golden path + 2–3 rules edge cases.
  - [ ] Maintenance scheduler happy path.
  - [ ] Telemetry ingest happy path.
  - [ ] Regulatory list endpoint.
  - [ ] Geospatial validation happy path.
  - [ ] Climate forecast happy path.
  - [ ] IoT device command happy path.
- [ ] Wire GitHub Actions with 40% gate; ratchet to 65% then 85%.
- [ ] Add OpenAPI contract tests and publish schema to MkDocs.

---

## Notes & Adaptation
- If your actual endpoints differ, adjust only the URL strings; the fixture and assertion patterns remain the same.
- For services that touch external APIs, prefer **adapter injection** so tests can pass a stub instead of network calls.
- For storage, abstract S3/MinIO access behind a small interface so the `S3Stub` can be dropped in during tests.

This pack is intentionally pragmatic: quick wins first, then depth. Drop these files in, tweak endpoint paths, and you should see coverage spike immediately.

