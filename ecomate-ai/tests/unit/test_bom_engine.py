# tests/unit/test_bom_engine.py
import pytest

# Assuming the function to be tested is in this path
from ecomate_ai.services.proposal.bom_engine import select_bom

@pytest.fixture
def mock_product_catalog():
    """Provides a mock product catalog for the BOM engine to use."""
    return {
        "SOLAR_GEYSER_200L": {"sku": "SG-200", "type": "geyser", "capacity_l": 200, "price": 800},
        "SOLAR_GEYSER_150L": {"sku": "SG-150", "type": "geyser", "capacity_l": 150, "price": 650},
        "HEAT_PUMP_5KW": {"sku": "HP-5", "type": "heat_pump", "power_kw": 5, "price": 1200},
        "GRID_TIE_INVERTER_3KW": {"sku": "GTI-3", "type": "inverter", "power_kw": 3, "price": 400},
        "BATTERY_5KWH": {"sku": "BAT-5", "type": "battery", "capacity_kwh": 5, "price": 2000},
        "MOUNTING_KIT_ROOF": {"sku": "MNT-R", "type": "mounting", "price": 150},
    }

def test_select_bom_200l_basic_case(mock_product_catalog):
    """Tests that a standard 200L system with grid connection selects the right components."""
    spec = {"hot_water_daily_l": 200, "grid_connection": True, "off_grid": False}
    
    # Mock the catalog lookup within the engine
    bom = select_bom(spec, catalog=mock_product_catalog)
    
    assert isinstance(bom, list)
    assert len(bom) > 0
    
    skus_in_bom = {item["sku"] for item in bom}
    
    # Check for expected components
    assert "SG-200" in skus_in_bom
    assert "GTI-3" in skus_in_bom
    assert "MNT-R" in skus_in_bom
    
    # Check that off-grid components are NOT included
    assert "BAT-5" not in skus_in_bom

def test_select_bom_off_grid_case(mock_product_catalog):
    """Tests that an off-grid system includes a battery."""
    spec = {"hot_water_daily_l": 150, "grid_connection": False, "off_grid": True}
    
    bom = select_bom(spec, catalog=mock_product_catalog)
    
    skus_in_bom = {item["sku"] for item in bom}
    
    assert "SG-150" in skus_in_bom
    assert "BAT-5" in skus_in_bom # Expect a battery for off-grid
    
    # Check that grid-tie components are NOT included
    assert "GTI-3" not in skus_in_bom

def test_select_bom_heat_pump_alternative(mock_product_catalog):
    """Tests that a heat pump is selected when solar is not feasible."""
    spec = {"hot_water_daily_l": 200, "grid_connection": True, "solar_feasible": False}
    
    bom = select_bom(spec, catalog=mock_product_catalog)
    
    skus_in_bom = {item["sku"] for item in bom}
    
    assert "HP-5" in skus_in_bom # Expect a heat pump
    
    # Check that solar components are NOT included
    assert "SG-200" not in skus_in_bom
