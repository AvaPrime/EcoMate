# simple rules for upsell/cross-sell/bundles

def suggest_bundle(sku: str) -> list[str]:
    if sku.startswith('PUMP'): return ['FILTER-SED-20', 'HOSE-FLEX-32MM']
    if sku.startswith('UV'): return ['SLEEVE-UV', 'LAMP-UV-80W']
    return []