# EcoMate – Production Implementation Plan (Drop-in Files & Steps)

This plan details the immediate implementation tasks to replace stub logic with production-ready code and establish EcoMate’s foundation.

---

## 1. Proposal Agent
- **Files:** `bom_engine.py`, `cost_model.py`
- **Tasks:**
  - Replace if/elif BOM selector with rules-based or API-driven selector.
  - Replace naive cost percentages with labor, logistics, and ops cost model.
- **Additions:** Vendor API connector integration, PDF proposal export with branding.

---

## 2. Catalog Agent
- **Files:** `sync.py`, `woocommerce.py`, `medusa.py`
- **Tasks:**
  - Implement normalization functions across connectors.
  - Ensure consistent schema for product ingestion.
- **Outputs:** Unified catalog JSON written to `/data/catalog/`.

---

## 3. Maintenance Scheduler
- **File:** `scheduler.py`
- **Tasks:**
  - Extend logic beyond fixed intervals.
  - Use asset age, condition, and usage factors.
  - Allow recurring PRs with monthly updates.

---

## 4. Compliance Agent
- **Files:** `rules/*.yaml`, `engine.py`
- **Tasks:**
  - Expand rulesets with SANS, ISO.
  - Implement evaluation engine with structured JSON output.
- **Outputs:** Compliance report (JSON + PDF) attached to PR.

---

## 5. Telemetry Agent
- **File:** `ingestor.py`
- **Tasks:**
  - Replace hardcoded EXPECTED dict with dynamic baselines.
  - Store in TimescaleDB/InfluxDB.
  - Generate Grafana dashboards.

---

## 6. Infrastructure & Tooling
- **Proposal Export**: Branded PDF generation (WeasyPrint preferred).
- **GitHub Actions**: Configure workflows to auto-open PRs from bot.
- **Telemetry DB**: Provision TimescaleDB with hypertables.
- **Grafana**: Add dashboards for flow, energy, compliance, maintenance KPIs.

---

## 7. Platform Enhancements
- **Advanced Bundling**: Expand `bundling.py` with recommendation logic.
- **AI/LLM Integration**: Deterministic parser-first with LLM fallback for natural language proposal requests.
- **Compliance by Construction**: Integrate compliance checks into proposal generation flow.

---

## 8. Acceptance Criteria
- PRs contain proposals with live pricing, compliance report, and telemetry baselines.
- Dashboards available for real-time metrics.
- CI/CD enforces compliance gate before merges.

---

## 9. Next Steps
- Build VendorClient abstraction and connect to first supplier.
- Deploy TimescaleDB + Grafana stack.
- Draft first compliance connectors (SANS water/electrical rules).
- Extend Scheduler with asset-based logic.

---

This implementation pack should be executed first, as it lays the groundwork for subsequent expansions in the roadmap.

