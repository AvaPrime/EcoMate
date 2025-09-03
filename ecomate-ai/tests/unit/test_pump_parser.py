"""Unit tests for pump parser components."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
import json
from pathlib import Path

from src.parsers.pumps import PumpParser
from src.models.product import PumpSpecification
from src.utils.exceptions import ParserError, ValidationError


class TestPumpParser:
    """Test cases for PumpParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a PumpParser instance for testing."""
        return PumpParser()
    
    @pytest.fixture
    def sample_html(self, test_fixtures_dir):
        """Load sample HTML fixture for testing."""
        html_file = test_fixtures_dir / "html_samples" / "grundfos_pumps.html"
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    @pytest.fixture
    def test_data(self, test_fixtures_dir):
        """Load test data from JSON fixture."""
        data_file = test_fixtures_dir / "test_data.json"
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_parser_initialization(self, parser):
        """Test parser initialization."""
        assert parser is not None
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'extract_specifications')
        assert hasattr(parser, 'normalize_units')
    
    def test_parse_valid_html(self, parser, sample_html):
        """Test parsing valid HTML with pump data."""
        results = parser.parse(sample_html, "https://www.grundfos.com/products")
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check first pump result
        pump = results[0]
        assert isinstance(pump, dict)
        assert 'name' in pump
        assert 'flow_rate_lpm' in pump
        assert 'head_meters' in pump
        assert 'power_kw' in pump
        assert 'price_usd' in pump
        assert 'supplier' in pump
    
    def test_parse_empty_html(self, parser):
        """Test parsing empty HTML."""
        empty_html = "<html><body></body></html>"
        results = parser.parse(empty_html, "https://example.com")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_parse_malformed_html(self, parser):
        """Test parsing malformed HTML."""
        malformed_html = "<table><tr><td>incomplete"
        
        with pytest.raises(ParserError):
            parser.parse(malformed_html, "https://example.com")
    
    def test_extract_specifications_valid_row(self, parser):
        """Test extracting specifications from valid table row."""
        html = """
        <tr class="pump-row">
            <td class="model">CR 3-8</td>
            <td class="flow">120</td>
            <td class="head">45</td>
            <td class="power">2.2</td>
            <td class="efficiency">85</td>
            <td class="price">$1,250.00</td>
            <td class="inlet">2"</td>
        </tr>
        """
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')
        
        specs = parser.extract_specifications(row)
        
        assert isinstance(specs, dict)
        assert specs['name'] == 'CR 3-8'
        assert specs['flow_rate_lpm'] == 120.0
        assert specs['head_meters'] == 45.0
        assert specs['power_kw'] == 2.2
        assert specs['efficiency_percent'] == 85.0
        assert specs['price_usd'] == 1250.00
    
    def test_extract_specifications_missing_data(self, parser):
        """Test extracting specifications with missing data."""
        html = """
        <tr class="pump-row">
            <td class="model">CR 3-8</td>
            <td class="flow"></td>
            <td class="head">45</td>
        </tr>
        """
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')
        
        with pytest.raises(ValidationError):
            parser.extract_specifications(row)
    
    def test_normalize_units_flow_rate(self, parser):
        """Test normalizing flow rate units."""
        test_cases = [
            ("120 L/min", 120.0),
            ("2.5 m³/h", 41.67),  # 2.5 * 1000 / 60
            ("500 GPM", 1892.71),  # 500 * 3.78541
            ("120", 120.0),  # Default L/min
        ]
        
        for input_val, expected in test_cases:
            result = parser.normalize_units(input_val, 'flow_rate')
            assert abs(result - expected) < 0.1
    
    def test_normalize_units_head(self, parser):
        """Test normalizing head units."""
        test_cases = [
            ("45 m", 45.0),
            ("150 ft", 45.72),  # 150 * 0.3048
            ("45", 45.0),  # Default meters
        ]
        
        for input_val, expected in test_cases:
            result = parser.normalize_units(input_val, 'head')
            assert abs(result - expected) < 0.1
    
    def test_normalize_units_power(self, parser):
        """Test normalizing power units."""
        test_cases = [
            ("2.2 kW", 2.2),
            ("2200 W", 2.2),
            ("3 HP", 2.24),  # 3 * 0.746
            ("2.2", 2.2),  # Default kW
        ]
        
        for input_val, expected in test_cases:
            result = parser.normalize_units(input_val, 'power')
            assert abs(result - expected) < 0.1
    
    def test_normalize_units_price(self, parser):
        """Test normalizing price units."""
        test_cases = [
            ("$1,250.00", 1250.00),
            ("€1,150.00", 1250.00),  # Mock conversion rate
            ("£1,000.00", 1250.00),  # Mock conversion rate
            ("1250", 1250.00),  # Default USD
        ]
        
        with patch('src.parsers.pumps.convert_currency') as mock_convert:
            mock_convert.return_value = 1250.00
            
            for input_val, expected in test_cases:
                result = parser.normalize_units(input_val, 'price')
                assert result == expected
    
    def test_normalize_units_invalid_type(self, parser):
        """Test normalizing units with invalid type."""
        with pytest.raises(ValueError):
            parser.normalize_units("123", 'invalid_type')
    
    def test_parse_with_supplier_detection(self, parser):
        """Test parsing with automatic supplier detection."""
        test_urls = [
            ("https://www.grundfos.com/products", "Grundfos"),
            ("https://www.xylem.com/pumps", "Xylem"),
            ("https://www.pentair.com/products", "Pentair"),
            ("https://unknown-supplier.com", "Unknown"),
        ]
        
        for url, expected_supplier in test_urls:
            with patch.object(parser, 'detect_supplier') as mock_detect:
                mock_detect.return_value = expected_supplier
                
                # Mock HTML with basic pump data
                html = """
                <table>
                    <tr><td>Test Pump</td><td>100</td><td>30</td><td>1.5</td><td>$800</td></tr>
                </table>
                """
                
                results = parser.parse(html, url)
                
                if results:  # Only check if parsing succeeded
                    assert results[0]['supplier'] == expected_supplier
    
    def test_parse_performance_large_dataset(self, parser):
        """Test parser performance with large dataset."""
        # Generate large HTML table
        rows = []
        for i in range(1000):
            rows.append(f"""
            <tr class="pump-row">
                <td class="model">Pump-{i}</td>
                <td class="flow">{100 + i}</td>
                <td class="head">{30 + i % 50}</td>
                <td class="power">{1.5 + i % 10}</td>
                <td class="efficiency">{80 + i % 15}</td>
                <td class="price">${800 + i * 10}</td>
            </tr>
            """)
        
        large_html = f"""
        <html>
        <body>
            <table class="pump-table">
                <thead>
                    <tr><th>Model</th><th>Flow</th><th>Head</th><th>Power</th><th>Efficiency</th><th>Price</th></tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        import time
        start_time = time.time()
        results = parser.parse(large_html, "https://example.com")
        end_time = time.time()
        
        # Should complete within reasonable time (< 5 seconds)
        assert (end_time - start_time) < 5.0
        assert len(results) == 1000
    
    def test_parse_with_different_table_structures(self, parser):
        """Test parsing different HTML table structures."""
        # Test vertical layout
        vertical_html = """
        <div class="pump-card">
            <h3>CR 3-8</h3>
            <div class="spec">Flow: 120 L/min</div>
            <div class="spec">Head: 45 m</div>
            <div class="spec">Power: 2.2 kW</div>
            <div class="price">$1,250</div>
        </div>
        """
        
        # Test list layout
        list_html = """
        <ul class="pump-list">
            <li class="pump-item">
                <span class="name">CR 3-8</span>
                <span class="flow">120 L/min</span>
                <span class="head">45 m</span>
                <span class="power">2.2 kW</span>
                <span class="price">$1,250</span>
            </li>
        </ul>
        """
        
        for html in [vertical_html, list_html]:
            results = parser.parse(html, "https://example.com")
            # Parser should handle different structures gracefully
            assert isinstance(results, list)
    
    def test_error_handling_network_issues(self, parser):
        """Test error handling for network-related issues."""
        # Test with None input
        with pytest.raises(ParserError):
            parser.parse(None, "https://example.com")
        
        # Test with invalid URL
        with pytest.raises(ParserError):
            parser.parse("<html></html>", "invalid-url")
    
    def test_specification_validation(self, parser):
        """Test specification validation."""
        valid_specs = {
            'name': 'Test Pump',
            'flow_rate_lpm': 120.0,
            'head_meters': 45.0,
            'power_kw': 2.2,
            'price_usd': 1250.00,
            'supplier': 'Test Supplier'
        }
        
        # Valid specs should pass
        validated = parser.validate_specifications(valid_specs)
        assert validated == valid_specs
        
        # Invalid specs should raise ValidationError
        invalid_specs = valid_specs.copy()
        invalid_specs['flow_rate_lpm'] = -10  # Negative flow rate
        
        with pytest.raises(ValidationError):
            parser.validate_specifications(invalid_specs)
    
    @pytest.mark.parametrize("test_case", [
        {"input": "CR 3-8", "expected": "CR 3-8"},
        {"input": "  CR 3-8  ", "expected": "CR 3-8"},
        {"input": "CR\n3-8", "expected": "CR 3-8"},
        {"input": "", "expected": None},
    ])
    def test_clean_text_data(self, parser, test_case):
        """Test text cleaning functionality."""
        result = parser.clean_text(test_case["input"])
        assert result == test_case["expected"]
    
    def test_parse_with_mock_data(self, parser, test_data):
        """Test parsing using mock data from fixtures."""
        pump_data = test_data['pumps']['grundfos'][0]
        
        # Create HTML from test data
        html = f"""
        <table class="pump-table">
            <tr class="pump-row">
                <td class="model">{pump_data['name']}</td>
                <td class="flow">{pump_data['flow_rate_lpm']}</td>
                <td class="head">{pump_data['head_meters']}</td>
                <td class="power">{pump_data['power_kw']}</td>
                <td class="efficiency">{pump_data['efficiency_percent']}</td>
                <td class="price">${pump_data['price_usd']}</td>
            </tr>
        </table>
        """
        
        results = parser.parse(html, "https://www.grundfos.com")
        
        assert len(results) == 1
        result = results[0]
        
        assert result['name'] == pump_data['name']
        assert result['flow_rate_lpm'] == pump_data['flow_rate_lpm']
        assert result['head_meters'] == pump_data['head_meters']
        assert result['power_kw'] == pump_data['power_kw']
        assert result['price_usd'] == pump_data['price_usd']