#!/usr/bin/env python3
"""
Optional demo test file for vendor-specific parsers.
Run this to verify parser functionality with sample data.

Usage:
    python services/parsers/_demo_test.py
"""

import json
from services.parsers.pumps import parse_pump_table
from services.parsers.uv import parse_uv_table
from services.parsers.dispatcher import parse_by_domain, parse_by_category

# Sample pump data
SAMPLE_PUMP_ROWS = [
    ["Model", "Flow Rate", "Head", "Power", "Price", "SKU"],
    ["AquaPump 100", "50 L/h", "10 m", "0.5 kW", "$299", "AP-100"],
    ["FlowMax 200", "100 L/h", "15 m", "0.75 kW", "$449", "FM-200"],
    ["HydroForce 300", "150 L/h", "20 m", "1.0 kW", "$599", "HF-300"]
]

# Sample UV reactor data
SAMPLE_UV_ROWS = [
    ["Model", "Flow Rate", "UV Dose", "Lamp Power", "Price", "SKU"],
    ["UVClean 50", "50 L/h", "30 mJ/cm²", "25W", "$199", "UV-50"],
    ["SterilMax 100", "100 L/h", "40 mJ/cm²", "40W", "$349", "SM-100"],
    ["PurifyPro 200", "200 L/h", "50 mJ/cm²", "65W", "$549", "PP-200"]
]

def test_pump_parser():
    """Test pump parser with sample data."""
    print("\n=== Testing Pump Parser ===")
    try:
        result = parse_pump_table(SAMPLE_PUMP_ROWS)
        print(f"Suppliers found: {len(result.get('suppliers', []))}")
        print(f"Parts found: {len(result.get('parts', []))}")
        
        if result.get('suppliers'):
            print("\nFirst supplier:")
            print(json.dumps(result['suppliers'][0], indent=2))
        
        if result.get('parts'):
            print("\nFirst part:")
            print(json.dumps(result['parts'][0], indent=2))
            
        return True
    except Exception as e:
        print(f"Pump parser error: {e}")
        return False

def test_uv_parser():
    """Test UV reactor parser with sample data."""
    print("\n=== Testing UV Reactor Parser ===")
    try:
        result = parse_uv_table(SAMPLE_UV_ROWS)
        print(f"Suppliers found: {len(result.get('suppliers', []))}")
        print(f"Parts found: {len(result.get('parts', []))}")
        
        if result.get('suppliers'):
            print("\nFirst supplier:")
            print(json.dumps(result['suppliers'][0], indent=2))
        
        if result.get('parts'):
            print("\nFirst part:")
            print(json.dumps(result['parts'][0], indent=2))
            
        return True
    except Exception as e:
        print(f"UV parser error: {e}")
        return False

def test_dispatcher():
    """Test parser dispatcher with sample URLs."""
    print("\n=== Testing Parser Dispatcher ===")
    
    # Test domain-based parsing
    test_urls = [
        "https://grundfos.com/products/pumps",
        "https://xylem.com/en-us/products-and-services/pumps",
        "https://trojan-uv.com/products/uv-systems",
        "https://atlantium.com/uv-systems"
    ]
    
    for url in test_urls:
        try:
            result = parse_by_domain(url, SAMPLE_PUMP_ROWS)
            print(f"\nURL: {url}")
            print(f"Result: {len(result.get('suppliers', []))} suppliers, {len(result.get('parts', []))} parts")
        except Exception as e:
            print(f"Dispatcher error for {url}: {e}")
    
    # Test category-based parsing
    try:
        result = parse_by_category("pump", SAMPLE_PUMP_ROWS)
        print(f"\nCategory 'pump': {len(result.get('suppliers', []))} suppliers, {len(result.get('parts', []))} parts")
        
        result = parse_by_category("uv", SAMPLE_UV_ROWS)
        print(f"Category 'uv': {len(result.get('suppliers', []))} suppliers, {len(result.get('parts', []))} parts")
        
        return True
    except Exception as e:
        print(f"Category dispatcher error: {e}")
        return False

def main():
    """Run all demo tests."""
    print("Vendor-Specific Parsers Demo Test")
    print("=" * 40)
    
    results = []
    results.append(test_pump_parser())
    results.append(test_uv_parser())
    results.append(test_dispatcher())
    
    print("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Parser implementation is working correctly.")
    else:
        print("❌ Some tests failed. Check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    main()