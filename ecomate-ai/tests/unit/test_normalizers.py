# tests/unit/test_normalizers.py
from decimal import Decimal, ROUND_HALF_UP

# Assuming the function to be tested is in this path
# This might need to be created if it doesn't exist.
from ecomate_ai.services.catalog.normalizers import normalize_price

def test_normalize_price_rounds_to_two_dp():
    """Tests that price normalization correctly rounds to two decimal places."""
    assert normalize_price(12.3456) == Decimal("12.35")
    assert normalize_price(99.999) == Decimal("100.00")
    assert normalize_price(1.004) == Decimal("1.00")

def test_normalize_price_with_decimal_input():
    """Tests that the function handles Decimal input correctly."""
    assert normalize_price(Decimal("45.678")) == Decimal("45.68")

def test_normalize_price_with_integer_input():
    """Tests that the function handles integer input correctly."""
    assert normalize_price(50) == Decimal("50.00")
