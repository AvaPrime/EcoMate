# EcoMate – Market & Supply Chain Data Integration

This document defines how EcoMate integrates real-time market and supply chain data to optimize proposals and catalog intelligence.

---

## 1. Vendor & Supplier APIs
**Purpose:** Replace static pricing with live supplier data.
- **Implementation:** Extend `bom_engine.py` and `cost_model.py` to call vendor APIs for pricing, stock, and logistics.
- **Abstraction:** Create `services/vendors/` with per-vendor connector modules and a `VendorClient` interface (`fetch_price`, `fetch_stock`, `fetch_logistics`).
- **Fallback:** Use cached or CSV data if API unavailable.

**Value:** Accurate, stock-aware proposals with precise logistics.

---

## 2. E-commerce Marketplace APIs
**Purpose:** Extend beyond internal sync to competitor monitoring.
- **Implementation:** Extend `sync.py` with competitor product monitoring via public APIs.
- **Storage:** Save competitor snapshots in `market_intel/` with JSON reports.
- **Reports:** Generate PRs comparing EcoMate pricing vs competitor averages.

**Value:** Competitive pricing and benchmarking intelligence.

---

## 3. Sourcing & Procurement Data
**Purpose:** Ensure resilience and cost optimization.
- **Implementation:** Add `services/procurement/alt_sourcing.py` to query Alibaba/local sourcing APIs.
- **Logic:** Define equivalence rules for alternative parts (e.g., power rating, flow capacity).
- **Workflow:** Proposal workflow suggests alternatives with human-in-the-loop approval.

**Value:** Resilient supply chain and margin optimization.

---

## 4. Integration Pattern
**File Layout:**
```
services/
  vendors/
    vendor_a.py
    vendor_b.py
  procurement/
    alt_sourcing.py
  catalog/
    sync.py
  proposal/
    bom_engine.py
    cost_model.py
```

**Workflow Hooks:**
- Proposal workflow → vendor API → cost_model.
- Catalog workflow → competitor sync → PR report.
- Maintenance workflow → sourcing if replacement needed.

**Caching Strategy:** Redis/local cache with TTL 15–30 min; nightly supplier refresh.

---

## 5. Next Steps
- Build `VendorClient` abstraction and first supplier connector.
- Replace BOM price lookup with live API call (with fallback).
- Extend `sync.py` with competitor monitoring.
- Implement alt-sourcing workflow for critical parts (e.g., blowers).

---

By implementing these integrations, EcoMate ensures proposals are market-aware, competitive, and resilient.

