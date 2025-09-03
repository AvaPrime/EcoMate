# tests/unit/test_cost_model.py
import pytest
from decimal import Decimal

# Assuming the function to be tested is in this path
from ecomate_ai.services.proposal.cost_model import estimate_cost

def test_estimate_cost_basic():
    """Tests basic cost estimation with a simple bill of materials."""
    bom = [{"sku": "A", "qty": 2, "unit_price": Decimal("100.00")}]
    
    out = estimate_cost(bom, labor_pct=Decimal("0.2"), overhead_pct=Decimal("0.1"))
    
    assert out["subtotal"] == Decimal("200.00")
    assert out["labor_cost"] == Decimal("40.00") # 20% of 200
    assert out["overhead_cost"] == Decimal("20.00") # 10% of 200
    assert out["total"] == Decimal("260.00") # 200 + 40 + 20

def test_estimate_cost_multiple_items():
    """Tests cost estimation with a more complex bill of materials."""
    bom = [
        {"sku": "PUMP-1", "qty": 1, "unit_price": Decimal("1500.50")},
        {"sku": "FILTER-3", "qty": 3, "unit_price": Decimal("75.25")},
        {"sku": "VALVE-T", "qty": 5, "unit_price": Decimal("30.00")},
    ]
    
    subtotal = Decimal("1500.50") + (3 * Decimal("75.25")) + (5 * Decimal("30.00"))
    # 1500.50 + 225.75 + 150.00 = 1876.25
    
    out = estimate_cost(bom, labor_pct=Decimal("0.15"), overhead_pct=Decimal("0.05"))
    
    assert out["subtotal"] == subtotal
    assert out["labor_cost"] == subtotal * Decimal("0.15")
    assert out["overhead_cost"] == subtotal * Decimal("0.05")
    assert out["total"] == subtotal * Decimal("1.20") # 1 + 0.15 + 0.05

def test_estimate_cost_zero_percentages():
    """Tests that zero labor and overhead percentages work correctly."""
    bom = [{"sku": "A", "qty": 1, "unit_price": Decimal("100.00")}]
    
    out = estimate_cost(bom, labor_pct=Decimal("0.0"), overhead_pct=Decimal("0.0"))
    
    assert out["subtotal"] == Decimal("100.00")
    assert out["labor_cost"] == Decimal("0.00")
    assert out["overhead_cost"] == Decimal("0.00")
    assert out["total"] == Decimal("100.00")

def test_estimate_cost_empty_bom():
    """Tests that an empty bill of materials results in zero cost."""
    bom = []
    out = estimate_cost(bom, labor_pct=Decimal("0.2"), overhead_pct=Decimal("0.1"))
    
    assert out["subtotal"] == Decimal("0.00")
    assert out["total"] == Decimal("0.00")
