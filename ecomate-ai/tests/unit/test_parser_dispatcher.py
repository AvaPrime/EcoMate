"""Unit tests for parser dispatcher component."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from pathlib import Path

from src.parsers.dispatcher import ParserDispatcher
from src.parsers.pumps import PumpParser
from src.parsers.uv_reactors import UVReactorParser
from src.parsers.llm_fallback import LLMFallbackParser
from src.utils.exceptions import ParserError, UnsupportedSupplierError


class TestParserDispatcher:
    """Test cases for ParserDispatcher class."""
    
    @pytest.fixture
    def dispatcher(self):
        """Create a ParserDispatcher instance for testing."""
        return ParserDispatcher()
    
    @pytest.fixture
    def test_data(self, test_fixtures_dir):
        """Load test data from JSON fixture."""
        data_file = test_fixtures_dir / "test_data.json"
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_dispatcher_initialization(self, dispatcher):
        """Test dispatcher initialization."""
        assert dispatcher is not None
        assert hasattr(dispatcher, 'dispatch')
        assert hasattr(dispatcher, 'detect_supplier')
        assert hasattr(dispatcher, 'detect_product_type')
        assert hasattr(dispatcher, 'get_parser')
    
    def test_detect_supplier_from_url(self, dispatcher):
        """Test supplier detection from URL."""
        test_cases = [
            ("https://www.grundfos.com/products/pumps", "Grundfos"),
            ("https://grundfos.com/cr-series", "Grundfos"),
            ("https://www.xylem.com/en-us/products/pumps", "Xylem"),
            ("https://xylem.com/lowara-pumps", "Xylem"),
            ("https://www.trojanuv.com/systems", "Trojan Technologies"),
            ("https://trojanuv.com/uv-reactors", "Trojan Technologies"),
            ("https://www.pentair.com/products", "Pentair"),
            ("https://www.wilo.com/pumps", "Wilo"),
            ("https://unknown-supplier.com/products", "Unknown"),
        ]
        
        for url, expected_supplier in test_cases:
            detected = dispatcher.detect_supplier(url)
            assert detected == expected_supplier
    
    def test_detect_product_type_from_url(self, dispatcher):
        """Test product type detection from URL."""
        test_cases = [
            ("https://www.grundfos.com/products/pumps", "pumps"),
            ("https://example.com/centrifugal-pumps", "pumps"),
            ("https://example.com/water-pumps", "pumps"),
            ("https://www.trojanuv.com/uv-systems", "uv"),
            ("https://example.com/uv-disinfection", "uv"),
            ("https://example.com/ultraviolet-reactors", "uv"),
            ("https://example.com/water-treatment", "general"),
            ("https://unknown.com/products", "general"),
        ]
        
        for url, expected_type in test_cases:
            detected = dispatcher.detect_product_type(url)
            assert detected == expected_type
    
    def test_detect_product_type_from_html(self, dispatcher):
        """Test product type detection from HTML content."""
        pump_html = """
        <html>
            <title>Centrifugal Pumps - High Efficiency</title>
            <body>
                <h1>Water Pumps</h1>
                <p>Flow rate, head, efficiency specifications</p>
                <table>
                    <tr><th>Model</th><th>Flow (L/min)</th><th>Head (m)</th></tr>
                </table>
            </body>
        </html>
        """
        
        uv_html = """
        <html>
            <title>UV Disinfection Systems</title>
            <body>
                <h1>Ultraviolet Reactors</h1>
                <p>UV dose, lamp count, disinfection efficiency</p>
                <table>
                    <tr><th>Model</th><th>Flow (L/min)</th><th>UV Dose (mJ/cm²)</th></tr>
                </table>
            </body>
        </html>
        """
        
        assert dispatcher.detect_product_type_from_html(pump_html) == "pumps"
        assert dispatcher.detect_product_type_from_html(uv_html) == "uv"
    
    def test_get_parser_for_known_suppliers(self, dispatcher):
        """Test getting appropriate parser for known suppliers."""
        # Test pump suppliers
        pump_suppliers = ["Grundfos", "Xylem", "Pentair", "Wilo"]
        for supplier in pump_suppliers:
            parser = dispatcher.get_parser(supplier, "pumps")
            assert isinstance(parser, PumpParser)
        
        # Test UV reactor suppliers
        uv_suppliers = ["Trojan Technologies", "Xylem", "Atlantium"]
        for supplier in uv_suppliers:
            parser = dispatcher.get_parser(supplier, "uv")
            assert isinstance(parser, UVReactorParser)
    
    def test_get_parser_for_unknown_supplier(self, dispatcher):
        """Test getting LLM fallback parser for unknown suppliers."""
        parser = dispatcher.get_parser("Unknown Supplier", "pumps")
        assert isinstance(parser, LLMFallbackParser)
        
        parser = dispatcher.get_parser("Unknown Supplier", "uv")
        assert isinstance(parser, LLMFallbackParser)
    
    def test_dispatch_pump_parsing(self, dispatcher, test_fixtures_dir):
        """Test dispatching pump parsing."""
        html_file = test_fixtures_dir / "html_samples" / "grundfos_pumps.html"
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        url = "https://www.grundfos.com/products/pumps"
        
        with patch.object(PumpParser, 'parse') as mock_parse:
            mock_parse.return_value = [
                {
                    'name': 'CR 3-8',
                    'supplier': 'Grundfos',
                    'flow_rate_lpm': 120.0,
                    'head_meters': 45.0,
                    'power_kw': 2.2,
                    'price_usd': 1250.00
                }
            ]
            
            results = dispatcher.dispatch(html_content, url)
            
            assert len(results) == 1
            assert results[0]['supplier'] == 'Grundfos'
            assert results[0]['name'] == 'CR 3-8'
            mock_parse.assert_called_once_with(html_content, url)
    
    def test_dispatch_uv_parsing(self, dispatcher, test_fixtures_dir):
        """Test dispatching UV reactor parsing."""
        html_file = test_fixtures_dir / "html_samples" / "trojan_uv.html"
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        url = "https://www.trojanuv.com/systems"
        
        with patch.object(UVReactorParser, 'parse') as mock_parse:
            mock_parse.return_value = [
                {
                    'name': 'UV3000Plus',
                    'supplier': 'Trojan Technologies',
                    'flow_rate_lpm': 500.0,
                    'uv_dose_mj_cm2': 40.0,
                    'power_kw': 1.8,
                    'lamp_count': 12,
                    'price_usd': 8500.00
                }
            ]
            
            results = dispatcher.dispatch(html_content, url)
            
            assert len(results) == 1
            assert results[0]['supplier'] == 'Trojan Technologies'
            assert results[0]['name'] == 'UV3000Plus'
            mock_parse.assert_called_once_with(html_content, url)
    
    def test_dispatch_llm_fallback(self, dispatcher):
        """Test dispatching to LLM fallback parser."""
        html_content = "<html><body><p>Unknown product data</p></body></html>"
        url = "https://unknown-supplier.com/products"
        
        with patch.object(LLMFallbackParser, 'parse') as mock_parse:
            mock_parse.return_value = [
                {
                    'name': 'Unknown Product',
                    'supplier': 'Unknown Supplier',
                    'category': 'water_treatment',
                    'extracted_data': {'raw_text': 'Unknown product data'}
                }
            ]
            
            results = dispatcher.dispatch(html_content, url)
            
            assert len(results) == 1
            assert results[0]['supplier'] == 'Unknown Supplier'
            mock_parse.assert_called_once_with(html_content, url)
    
    def test_dispatch_with_test_scenarios(self, dispatcher, test_data):
        """Test dispatch using test scenarios from fixtures."""
        scenarios = test_data['test_scenarios']['parser_dispatch']
        
        for scenario in scenarios:
            url = scenario['url']
            expected_parser = scenario['expected_parser']
            expected_supplier = scenario['expected_supplier']
            
            # Mock the parsing methods
            with patch.object(PumpParser, 'parse') as mock_pump_parse, \
                 patch.object(UVReactorParser, 'parse') as mock_uv_parse, \
                 patch.object(LLMFallbackParser, 'parse') as mock_llm_parse:
                
                # Set up mock returns
                mock_pump_parse.return_value = [{'supplier': expected_supplier, 'category': 'pump'}]
                mock_uv_parse.return_value = [{'supplier': expected_supplier, 'category': 'uv'}]
                mock_llm_parse.return_value = [{'supplier': expected_supplier, 'category': 'unknown'}]
                
                html_content = "<html><body>Test content</body></html>"
                results = dispatcher.dispatch(html_content, url)
                
                # Verify correct parser was called
                if expected_parser == 'pumps':
                    mock_pump_parse.assert_called_once()
                elif expected_parser == 'uv':
                    mock_uv_parse.assert_called_once()
                elif expected_parser == 'llm_fallback':
                    mock_llm_parse.assert_called_once()
    
    def test_supplier_domain_mapping(self, dispatcher):
        """Test supplier detection from domain mapping."""
        # Test the internal domain mapping
        domain_tests = [
            ("grundfos.com", "Grundfos"),
            ("xylem.com", "Xylem"),
            ("trojanuv.com", "Trojan Technologies"),
            ("pentair.com", "Pentair"),
            ("wilo.com", "Wilo"),
            ("unknown-domain.com", "Unknown"),
        ]
        
        for domain, expected_supplier in domain_tests:
            url = f"https://www.{domain}/products"
            detected = dispatcher.detect_supplier(url)
            assert detected == expected_supplier
    
    def test_product_type_keywords(self, dispatcher):
        """Test product type detection using keywords."""
        keyword_tests = [
            ("centrifugal pump specifications", "pumps"),
            ("water pump efficiency", "pumps"),
            ("submersible pump catalog", "pumps"),
            ("UV disinfection system", "uv"),
            ("ultraviolet reactor specifications", "uv"),
            ("UV lamp technology", "uv"),
            ("water treatment solutions", "general"),
            ("filtration systems", "general"),
        ]
        
        for text, expected_type in keyword_tests:
            html = f"<html><body><h1>{text}</h1></body></html>"
            detected = dispatcher.detect_product_type_from_html(html)
            assert detected == expected_type
    
    def test_error_handling_invalid_input(self, dispatcher):
        """Test error handling for invalid inputs."""
        # Test with None HTML
        with pytest.raises(ParserError):
            dispatcher.dispatch(None, "https://example.com")
        
        # Test with empty HTML
        results = dispatcher.dispatch("", "https://example.com")
        assert isinstance(results, list)
        assert len(results) == 0
        
        # Test with invalid URL
        with pytest.raises(ParserError):
            dispatcher.dispatch("<html></html>", "invalid-url")
    
    def test_parser_caching(self, dispatcher):
        """Test parser instance caching for performance."""
        # Get parser instances multiple times
        parser1 = dispatcher.get_parser("Grundfos", "pumps")
        parser2 = dispatcher.get_parser("Grundfos", "pumps")
        
        # Should return the same instance (cached)
        assert parser1 is parser2
        
        # Different supplier should return different instance
        parser3 = dispatcher.get_parser("Xylem", "pumps")
        assert parser1 is not parser3
    
    def test_dispatch_with_mixed_content(self, dispatcher):
        """Test dispatching with mixed product content."""
        mixed_html = """
        <html>
        <body>
            <h1>Water Treatment Products</h1>
            <div class="pumps-section">
                <h2>Centrifugal Pumps</h2>
                <table>
                    <tr><td>CR 3-8</td><td>120 L/min</td><td>45 m</td></tr>
                </table>
            </div>
            <div class="uv-section">
                <h2>UV Disinfection</h2>
                <table>
                    <tr><td>UV3000</td><td>500 L/min</td><td>40 mJ/cm²</td></tr>
                </table>
            </div>
        </body>
        </html>
        """
        
        url = "https://www.xylem.com/products"
        
        # Should detect primary product type and use appropriate parser
        results = dispatcher.dispatch(mixed_html, url)
        assert isinstance(results, list)
    
    def test_confidence_scoring(self, dispatcher):
        """Test confidence scoring for parser selection."""
        # Test high confidence scenarios
        high_confidence_cases = [
            ("https://www.grundfos.com/pumps", "Grundfos", "pumps"),
            ("https://www.trojanuv.com/uv-systems", "Trojan Technologies", "uv"),
        ]
        
        for url, expected_supplier, expected_type in high_confidence_cases:
            confidence = dispatcher.calculate_confidence(url, expected_supplier, expected_type)
            assert confidence > 0.8  # High confidence threshold
        
        # Test low confidence scenarios
        low_confidence_cases = [
            ("https://unknown.com/products", "Unknown", "general"),
        ]
        
        for url, expected_supplier, expected_type in low_confidence_cases:
            confidence = dispatcher.calculate_confidence(url, expected_supplier, expected_type)
            assert confidence < 0.5  # Low confidence threshold
    
    def test_dispatch_performance(self, dispatcher):
        """Test dispatcher performance with multiple requests."""
        import time
        
        html_content = "<html><body><h1>Test Product</h1></body></html>"
        urls = [
            "https://www.grundfos.com/pumps",
            "https://www.xylem.com/products",
            "https://www.trojanuv.com/systems",
        ] * 10  # 30 total requests
        
        start_time = time.time()
        
        for url in urls:
            with patch.object(PumpParser, 'parse', return_value=[]), \
                 patch.object(UVReactorParser, 'parse', return_value=[]), \
                 patch.object(LLMFallbackParser, 'parse', return_value=[]):
                dispatcher.dispatch(html_content, url)
        
        end_time = time.time()
        
        # Should complete within reasonable time (< 1 second for 30 requests)
        assert (end_time - start_time) < 1.0
    
    def test_dispatch_with_custom_parser_config(self, dispatcher):
        """Test dispatch with custom parser configuration."""
        # Test custom supplier mapping
        custom_config = {
            'suppliers': {
                'custom-supplier.com': 'Custom Supplier'
            },
            'product_types': {
                'custom-product': 'pumps'
            }
        }
        
        dispatcher.update_config(custom_config)
        
        detected_supplier = dispatcher.detect_supplier("https://custom-supplier.com/products")
        assert detected_supplier == "Custom Supplier"
    
    @pytest.mark.parametrize("url,expected_supplier,expected_type", [
        ("https://www.grundfos.com/cr-pumps", "Grundfos", "pumps"),
        ("https://www.xylem.com/lowara-pumps", "Xylem", "pumps"),
        ("https://www.trojanuv.com/uv3000", "Trojan Technologies", "uv"),
        ("https://unknown.com/water-treatment", "Unknown", "general"),
    ])
    def test_dispatch_parametrized(self, dispatcher, url, expected_supplier, expected_type):
        """Parametrized test for dispatch functionality."""
        html_content = "<html><body>Test content</body></html>"
        
        detected_supplier = dispatcher.detect_supplier(url)
        detected_type = dispatcher.detect_product_type(url)
        
        assert detected_supplier == expected_supplier
        assert detected_type == expected_type