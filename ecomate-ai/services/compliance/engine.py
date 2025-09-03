import yaml

def load_rules(name: str) -> dict:
    with open(f'services/compliance/rules/{name}.yaml','r',encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def evaluate(spec: dict, rules: dict) -> list[dict]:
    findings = []
    if 'uv_dose_mj_cm2' in spec and 'min_uv_dose_mj_cm2' in rules:
        ok = spec['uv_dose_mj_cm2'] >= rules['min_uv_dose_mj_cm2']
        findings.append({"rule":"uv_dose","ok": ok, "value": spec['uv_dose_mj_cm2'], "min": rules['min_uv_dose_mj_cm2']})
    return findings