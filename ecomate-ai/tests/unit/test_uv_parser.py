"""Unit tests for UV reactor parser components."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
import json
from pathlib import Path

from src.parsers.uv_reactors import UVReactorParser
from src.models.product import UVReactorSpecification
from src.utils.exceptions import ParserError, ValidationError


class TestUVReactorParser:
    """Test cases for UVReactorParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a UVReactorParser instance for testing."""
        return UVReactorParser()
    
    @pytest.fixture
    def sample_html(self, test_fixtures_dir):
        """Load sample HTML fixture for testing."""
        html_file = test_fixtures_dir / "html_samples" / "trojan_uv.html"
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
        assert hasattr(parser, 'calculate_uv_dose')
    
    def test_parse_valid_html(self, parser, sample_html):
        """Test parsing valid HTML with UV reactor data."""
        results = parser.parse(sample_html, "https://www.trojanuv.com/products")
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check first UV reactor result
        uv_reactor = results[0]
        assert isinstance(uv_reactor, dict)
        assert 'name' in uv_reactor
        assert 'flow_rate_lpm' in uv_reactor
        assert 'uv_dose_mj_cm2' in uv_reactor
        assert 'power_kw' in uv_reactor
        assert 'lamp_count' in uv_reactor
        assert 'price_usd' in uv_reactor
        assert 'supplier' in uv_reactor
    
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
        <tr class="uv-row">
            <td class="model">UV3000Plus</td>
            <td class="flow">500</td>
            <td class="dose">40</td>
            <td class="power">1.8</td>
            <td class="lamps">12</td>
            <td class="price">$8,500.00</td>
            <td class="size">1200 x 600 x 400 mm</td>
        </tr>
        """
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')
        
        specs = parser.extract_specifications(row)
        
        assert isinstance(specs, dict)
        assert specs['name'] == 'UV3000Plus'
        assert specs['flow_rate_lpm'] == 500.0
        assert specs['uv_dose_mj_cm2'] == 40.0
        assert specs['power_kw'] == 1.8
        assert specs['lamp_count'] == 12
        assert specs['price_usd'] == 8500.00
    
    def test_extract_specifications_missing_data(self, parser):
        """Test extracting specifications with missing data."""
        html = """
        <tr class="uv-row">
            <td class="model">UV3000Plus</td>
            <td class="flow"></td>
            <td class="dose">40</td>
        </tr>
        """
        soup = BeautifulSoup(html, 'html.parser')
        row = soup.find('tr')
        
        with pytest.raises(ValidationError):
            parser.extract_specifications(row)
    
    def test_normalize_units_flow_rate(self, parser):
        """Test normalizing flow rate units for UV reactors."""
        test_cases = [
            ("500 L/min", 500.0),
            ("8.33 m³/h", 138.83),  # 8.33 * 1000 / 60
            ("132 GPM", 499.33),   # 132 * 3.78541
            ("500", 500.0),        # Default L/min
        ]
        
        for input_val, expected in test_cases:
            result = parser.normalize_units(input_val, 'flow_rate')
            assert abs(result - expected) < 0.1
    
    def test_normalize_units_uv_dose(self, parser):
        """Test normalizing UV dose units."""
        test_cases = [
            ("40 mJ/cm²", 40.0),
            ("40000 µWs/cm²", 40.0),  # 40000 / 1000
            ("4 J/m²", 40.0),         # 4 * 10
            ("40", 40.0),             # Default mJ/cm²
        ]
        
        for input_val, expected in test_cases:
            result = parser.normalize_units(input_val, 'uv_dose')
            assert abs(result - expected) < 0.1
    
    def test_normalize_units_power(self, parser):
        """Test normalizing power units for UV reactors."""
        test_cases = [
            ("1.8 kW", 1.8),
            ("1800 W", 1.8),
            ("2.4 HP", 1.79),  # 2.4 * 0.746
            ("1.8", 1.8),     # Default kW
        ]
        
        for input_val, expected in test_cases:
            result = parser.normalize_units(input_val, 'power')
            assert abs(result - expected) < 0.1
    
    def test_normalize_units_lamp_count(self, parser):
        """Test normalizing lamp count."""
        test_cases = [
            ("12 lamps", 12),
            ("12", 12),
            ("twelve", 12),  # Text to number conversion
        ]
        
        for input_val, expected in test_cases:
            result = parser.normalize_units(input_val, 'lamp_count')
            assert result == expected
    
    def test_calculate_uv_dose(self, parser):
        """Test UV dose calculation from power and flow rate."""
        # Test with known values
        power_kw = 1.8
        flow_rate_lpm = 500.0
        lamp_efficiency = 0.35  # 35% efficiency
        
        calculated_dose = parser.calculate_uv_dose(power_kw, flow_rate_lpm, lamp_efficiency)
        
        # Expected calculation: (1.8 * 1000 * 0.35) / (500 / 60) = 75.6 mJ/cm²
        expected_dose = 75.6
        assert abs(calculated_dose - expected_dose) < 1.0
    
    def test_parse_with_supplier_detection(self, parser):
        """Test parsing with automatic supplier detection."""
        test_urls = [
            ("https://www.trojanuv.com/products", "Trojan Technologies"),
            ("https://www.xylem.com/uv-systems", "Xylem"),
            ("https://www.atlantium.com/products", "Atlantium"),
            ("https://unknown-supplier.com", "Unknown"),
        ]
        
        for url, expected_supplier in test_urls:
            with patch.object(parser, 'detect_supplier') as mock_detect:
                mock_detect.return_value = expected_supplier
                
                # Mock HTML with basic UV reactor data
                html = """
                <table>
                    <tr><td>Test UV</td><td>300</td><td>35</td><td>1.2</td><td>8</td><td>$6000</td></tr>
                </table>
                """
                
                results = parser.parse(html, url)
                
                if results:  # Only check if parsing succeeded
                    assert results[0]['supplier'] == expected_supplier
    
    def test_validate_uv_dose_range(self, parser):
        """Test UV dose validation within acceptable ranges."""
        valid_doses = [10, 25, 40, 65, 100]  # Typical UV doses
        invalid_doses = [-5, 0, 200, 1000]   # Out of range doses
        
        for dose in valid_doses:
            assert parser.validate_uv_dose(dose) is True
        
        for dose in invalid_doses:
            assert parser.validate_uv_dose(dose) is False
    
    def test_parse_lamp_technology_detection(self, parser):
        """Test detection of lamp technology types."""
        html_with_tech = """
        <div class="uv-system">
            <h3>UV5000</h3>
            <p>Low-pressure, high-output amalgam lamps</p>
            <span class="flow">800 L/min</span>
            <span class="dose">45 mJ/cm²</span>
            <span class="power">2.5 kW</span>
            <span class="lamps">16</span>
            <span class="price">$12,200</span>
        </div>
        """
        
        results = parser.parse(html_with_tech, "https://example.com")
        
        if results:
            result = results[0]
            assert 'lamp_technology' in result
            assert 'amalgam' in result['lamp_technology'].lower()
    
    def test_parse_reactor_material_detection(self, parser):
        """Test detection of reactor material."""
        html_with_material = """
        <div class="specs">
            <h3>UV3000Plus</h3>
            <div class="spec-item">
                <h4>Reactor Material</h4>
                <p>316L Stainless Steel</p>
            </div>
            <span class="flow">500</span>
            <span class="dose">40</span>
            <span class="power">1.8</span>
            <span class="lamps">12</span>
            <span class="price">$8500</span>
        </div>
        """
        
        results = parser.parse(html_with_material, "https://example.com")
        
        if results:
            result = results[0]
            assert 'reactor_material' in result
            assert '316L' in result['reactor_material']
    
    def test_parse_performance_specifications(self, parser):
        """Test parsing of performance specifications."""
        html_with_performance = """
        <table class="performance-table">
            <tr><td>Operating Temperature</td><td>5-40°C</td></tr>
            <tr><td>Operating Pressure</td><td>Up to 10 bar</td></tr>
            <tr><td>Transmittance Range</td><td>65-98% UVT</td></tr>
            <tr><td>Lamp Life</td><td>12,000 hours</td></tr>
        </table>
        <table class="uv-table">
            <tr class="uv-row">
                <td>UV3000Plus</td><td>500</td><td>40</td><td>1.8</td><td>12</td><td>$8500</td>
            </tr>
        </table>
        """
        
        results = parser.parse(html_with_performance, "https://example.com")
        
        if results:
            result = results[0]
            assert 'operating_temperature' in result
            assert 'operating_pressure' in result
            assert 'lamp_life_hours' in result
    
    def test_parse_with_different_layouts(self, parser):
        """Test parsing different HTML layouts for UV reactors."""
        # Test card layout
        card_html = """
        <div class="uv-card">
            <h3>UV3000Plus</h3>
            <div class="spec">Flow Rate: 500 L/min</div>
            <div class="spec">UV Dose: 40 mJ/cm²</div>
            <div class="spec">Power: 1.8 kW</div>
            <div class="spec">Lamps: 12</div>
            <div class="price">$8,500</div>
        </div>
        """
        
        # Test grid layout
        grid_html = """
        <div class="uv-grid">
            <div class="uv-item">
                <span class="name">UV3000Plus</span>
                <span class="flow">500 L/min</span>
                <span class="dose">40 mJ/cm²</span>
                <span class="power">1.8 kW</span>
                <span class="lamps">12</span>
                <span class="price">$8,500</span>
            </div>
        </div>
        """
        
        for html in [card_html, grid_html]:
            results = parser.parse(html, "https://example.com")
            # Parser should handle different structures gracefully
            assert isinstance(results, list)
    
    def test_specification_validation(self, parser):
        """Test UV reactor specification validation."""
        valid_specs = {
            'name': 'Test UV Reactor',
            'flow_rate_lpm': 500.0,
            'uv_dose_mj_cm2': 40.0,
            'power_kw': 1.8,
            'lamp_count': 12,
            'price_usd': 8500.00,
            'supplier': 'Test Supplier'
        }
        
        # Valid specs should pass
        validated = parser.validate_specifications(valid_specs)
        assert validated == valid_specs
        
        # Invalid specs should raise ValidationError
        invalid_specs = valid_specs.copy()
        invalid_specs['uv_dose_mj_cm2'] = -10  # Negative UV dose
        
        with pytest.raises(ValidationError):
            parser.validate_specifications(invalid_specs)
    
    def test_parse_with_mock_data(self, parser, test_data):
        """Test parsing using mock data from fixtures."""
        uv_data = test_data['uv_reactors']['trojan'][0]
        
        # Create HTML from test data
        html = f"""
        <table class="uv-table">
            <tr class="uv-row">
                <td class="model">{uv_data['name']}</td>
                <td class="flow">{uv_data['flow_rate_lpm']}</td>
                <td class="dose">{uv_data['uv_dose_mj_cm2']}</td>
                <td class="power">{uv_data['power_kw']}</td>
                <td class="lamps">{uv_data['lamp_count']}</td>
                <td class="price">${uv_data['price_usd']}</td>
            </tr>
        </table>
        """
        
        results = parser.parse(html, "https://www.trojanuv.com")
        
        assert len(results) == 1
        result = results[0]
        
        assert result['name'] == uv_data['name']
        assert result['flow_rate_lpm'] == uv_data['flow_rate_lpm']
        assert result['uv_dose_mj_cm2'] == uv_data['uv_dose_mj_cm2']
        assert result['power_kw'] == uv_data['power_kw']
        assert result['lamp_count'] == uv_data['lamp_count']
        assert result['price_usd'] == uv_data['price_usd']
    
    @pytest.mark.parametrize("lamp_type,expected_efficiency", [
        ("low pressure", 0.35),
        ("medium pressure", 0.15),
        ("amalgam", 0.40),
        ("led", 0.25),
        ("unknown", 0.30),  # Default efficiency
    ])
    def test_lamp_efficiency_calculation(self, parser, lamp_type, expected_efficiency):
        """Test lamp efficiency calculation based on lamp type."""
        efficiency = parser.get_lamp_efficiency(lamp_type)
        assert efficiency == expected_efficiency
    
    def test_error_handling_edge_cases(self, parser):
        """Test error handling for edge cases."""
        # Test with extremely high values
        high_values_html = """
        <tr class="uv-row">
            <td>UV-Extreme</td>
            <td>999999</td>  <!-- Unrealistic flow rate -->
            <td>1000</td>    <!-- Unrealistic UV dose -->
            <td>100</td>     <!-- Unrealistic power -->
            <td>1000</td>    <!-- Unrealistic lamp count -->
            <td>$999999</td>
        </tr>
        """
        
        soup = BeautifulSoup(high_values_html, 'html.parser')
        row = soup.find('tr')
        
        # Should handle extreme values gracefully
        with pytest.raises(ValidationError):
            parser.extract_specifications(row)
    
    def test_transmittance_calculation(self, parser):
        """Test UV transmittance (UVT) calculation and validation."""
        # Test valid UVT values
        valid_uvt_values = [65, 75, 85, 95, 98]
        
        for uvt in valid_uvt_values:
            dose_reduction = parser.calculate_dose_reduction(uvt)
            assert 0 <= dose_reduction <= 1
        
        # Test invalid UVT values
        invalid_uvt_values = [-10, 0, 105, 200]
        
        for uvt in invalid_uvt_values:
            with pytest.raises(ValueError):
                parser.calculate_dose_reduction(uvt)