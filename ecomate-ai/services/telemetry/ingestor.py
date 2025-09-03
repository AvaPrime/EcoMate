EXPECTED = {"flow_m3h": 15.0, "uv_dose_mj_cm2": 40.0}

def alert_findings(metrics: dict, headroom: float = 0.8):
    findings = []
    for k, exp in EXPECTED.items():
        val = metrics.get(k)
        if val is None: continue
        if val < exp * headroom:
            findings.append({"metric": k, "value": val, "expected": exp, "status": "low"})
    return findings