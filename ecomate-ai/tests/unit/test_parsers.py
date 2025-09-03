"""Unit tests for the parsers module.

These tests verify the parsing functionality for different data formats
and sources including HTML, PDF, CSV, and API responses.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO

from tests.test_utils import DataGenerator, ValidationHelper
from tests.factories import create_test_product


class TestHTMLParser:
    """Unit tests for HTML parsing functionality."""
    
    def test_parse_product_table_success(self, sample_html_table):
        """Test successful parsing of product table from HTML."""
        # Mock the HTML parser
        with patch('services.parsers.html_parser.BeautifulSoup') as mock_soup:
            mock_table = Mock()
            mock_rows = [
                Mock(find_all=Mock(return_value=[
                    Mock(get_text=Mock(return_value="Pump Model A")),
                    Mock(get_text=Mock(return_value="1000")),
                    Mock(get_text=Mock(return_value="50")),
                    Mock(get_text=Mock(return_value="$5000"))
                ])),
                Mock(find_all=Mock(return_value=[
                    Mock(get_text=Mock(return_value="Pump Model B")),
                    Mock(get_text=Mock(return_value="1200")),
                    Mock(get_text=Mock(return_value="60")),
                    Mock(get_text=Mock(return_value="$6000"))
                ]))
            ]
            mock_table.find_all.return_value = mock_rows
            mock_soup.return_value.find.return_value = mock_table
            
            # Import and test the parser
            from services.parsers.html_parser import HTMLParser
            parser = HTMLParser()
            
            result = parser.parse_product_table(sample_html_table)
            
            assert len(result) == 2
            assert result[0]["name"] == "Pump Model A"
            assert result[0]["flow_rate"] == "1000"
            assert result[0]["head_pressure"] == "50"
            assert result[0]["price"] == "$5000"
    
    def test_parse_product_specifications(self):
        """Test parsing product specifications from HTML."""
        html_content = """
        <div class="specifications">
            <div class="spec-item">
                <span class="spec-name">Flow Rate:</span>
                <span class="spec-value">1000 L/min</span>
            </div>
            <div class="spec-item">
                <span class="spec-name">Head Pressure:</span>
                <span class="spec-value">50 m</span>
            </div>
            <div class="spec-item">
                <span class="spec-name">Power:</span>
                <span class="spec-value">5.5 kW</span>
            </div>
        </div>
        """
        
        with patch('services.parsers.html_parser.BeautifulSoup') as mock_soup:
            # Mock the BeautifulSoup parsing
            mock_specs = [
                Mock(
                    find=Mock(side_effect=lambda cls: 
                        Mock(get_text=Mock(return_value="Flow Rate:")) if cls == "spec-name" 
                        else Mock(get_text=Mock(return_value="1000 L/min"))
                    )
                ),
                Mock(
                    find=Mock(side_effect=lambda cls: 
                        Mock(get_text=Mock(return_value="Head Pressure:")) if cls == "spec-name" 
                        else Mock(get_text=Mock(return_value="50 m"))
                    )
                ),
                Mock(
                    find=Mock(side_effect=lambda cls: 
                        Mock(get_text=Mock(return_value="Power:")) if cls == "spec-name" 
                        else Mock(get_text=Mock(return_value="5.5 kW"))
                    )
                )
            ]
            mock_soup.return_value.find_all.return_value = mock_specs
            
            from services.parsers.html_parser import HTMLParser
            parser = HTMLParser()
            
            result = parser.parse_specifications(html_content)
            
            assert "flow_rate" in result
            assert "head_pressure" in result
            assert "power" in result
            assert result["flow_rate"] == "1000 L/min"
            assert result["head_pressure"] == "50 m"
            assert result["power"] == "5.5 kW"
    
    def test_parse_malformed_html(self):
        """Test parsing malformed HTML gracefully."""
        malformed_html = "<table><tr><td>Incomplete"
        
        with patch('services.parsers.html_parser.BeautifulSoup') as mock_soup:
            mock_soup.return_value.find.return_value = None
            
            from services.parsers.html_parser import HTMLParser
            parser = HTMLParser()
            
            result = parser.parse_product_table(malformed_html)
            
            assert result == []
    
    def test_extract_product_links(self):
        """Test extracting product links from HTML."""
        with patch('services.parsers.html_parser.BeautifulSoup') as mock_soup:
            mock_links = [
                Mock(get=Mock(return_value="/products/pump-123"), get_text=Mock(return_value="Pump 123")),
                Mock(get=Mock(return_value="/products/uv-456"), get_text=Mock(return_value="UV Reactor 456")),
                Mock(get=Mock(return_value="/products/filter-789"), get_text=Mock(return_value="Filter 789"))
            ]
            mock_soup.return_value.find_all.return_value = mock_links
            
            from services.parsers.html_parser import HTMLParser
            parser = HTMLParser()
            
            result = parser.extract_product_links("<html>mock</html>")
            
            assert len(result) == 3
            assert result[0]["url"] == "/products/pump-123"
            assert result[0]["title"] == "Pump 123"


class TestCSVParser:
    """Unit tests for CSV parsing functionality."""
    
    def test_parse_product_csv_success(self):
        """Test successful parsing of product CSV data."""
        csv_data = """name,product_type,flow_rate_lpm,head_pressure_m,price_usd
Pump A,pump,1000,50,5000
Pump B,pump,1200,60,6000
UV Reactor C,uv_reactor,800,0,3000"""
        
        with patch('pandas.read_csv') as mock_read_csv:
            mock_df = pd.DataFrame({
                'name': ['Pump A', 'Pump B', 'UV Reactor C'],
                'product_type': ['pump', 'pump', 'uv_reactor'],
                'flow_rate_lpm': [1000, 1200, 800],
                'head_pressure_m': [50, 60, 0],
                'price_usd': [5000, 6000, 3000]
            })
            mock_read_csv.return_value = mock_df
            
            from services.parsers.csv_parser import CSVParser
            parser = CSVParser()
            
            result = parser.parse_products(StringIO(csv_data))
            
            assert len(result) == 3
            assert result[0]['name'] == 'Pump A'
            assert result[0]['product_type'] == 'pump'
            assert result[0]['flow_rate_lpm'] == 1000
    
    def test_parse_csv_with_missing_columns(self):
        """Test CSV parsing with missing required columns."""
        csv_data = """name,price_usd
Pump A,5000
Pump B,6000"""
        
        with patch('pandas.read_csv') as mock_read_csv:
            mock_df = pd.DataFrame({
                'name': ['Pump A', 'Pump B'],
                'price_usd': [5000, 6000]
            })
            mock_read_csv.return_value = mock_df
            
            from services.parsers.csv_parser import CSVParser
            parser = CSVParser()
            
            with pytest.raises(ValueError, match="Missing required columns"):
                parser.parse_products(StringIO(csv_data))
    
    def test_parse_csv_with_invalid_data_types(self):
        """Test CSV parsing with invalid data types."""
        csv_data = """name,product_type,flow_rate_lpm,price_usd
Pump A,pump,invalid_flow,5000
Pump B,pump,1200,invalid_price"""
        
        with patch('pandas.read_csv') as mock_read_csv:
            mock_df = pd.DataFrame({
                'name': ['Pump A', 'Pump B'],
                'product_type': ['pump', 'pump'],
                'flow_rate_lpm': ['invalid_flow', 1200],
                'price_usd': [5000, 'invalid_price']
            })
            mock_read_csv.return_value = mock_df
            
            from services.parsers.csv_parser import CSVParser
            parser = CSVParser()
            
            result = parser.parse_products(StringIO(csv_data))
            
            # Should skip invalid rows or handle gracefully
            assert len(result) <= 2
            # Valid row should be preserved
            valid_rows = [r for r in result if isinstance(r.get('flow_rate_lpm'), (int, float))]
            assert len(valid_rows) >= 1


class TestJSONParser:
    """Unit tests for JSON parsing functionality."""
    
    def test_parse_api_response_success(self):
        """Test successful parsing of API JSON response."""
        api_response = {
            "products": [
                {
                    "id": "pump-001",
                    "name": "Centrifugal Pump CP-100",
                    "type": "pump",
                    "specifications": {
                        "flow_rate": 1000,
                        "head_pressure": 50,
                        "power": 5.5
                    },
                    "price": {"amount": 5000, "currency": "USD"}
                }
            ],
            "total": 1,
            "page": 1
        }
        
        from services.parsers.json_parser import JSONParser
        parser = JSONParser()
        
        result = parser.parse_api_response(api_response)
        
        assert len(result) == 1
        assert result[0]["id"] == "pump-001"
        assert result[0]["name"] == "Centrifugal Pump CP-100"
        assert result[0]["specifications"]["flow_rate"] == 1000
    
    def test_parse_nested_json_structure(self):
        """Test parsing complex nested JSON structures."""
        complex_json = {
            "catalog": {
                "categories": {
                    "pumps": {
                        "products": [
                            {
                                "model": "CP-100",
                                "specs": {"flow": 1000, "pressure": 50}
                            }
                        ]
                    }
                }
            }
        }
        
        from services.parsers.json_parser import JSONParser
        parser = JSONParser()
        
        result = parser.extract_products_from_nested(complex_json)
        
        assert len(result) == 1
        assert result[0]["model"] == "CP-100"
        assert result[0]["specs"]["flow"] == 1000
    
    def test_parse_invalid_json(self):
        """Test handling of invalid JSON data."""
        from services.parsers.json_parser import JSONParser
        parser = JSONParser()
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            parser.parse_api_response("invalid json string")


class TestPDFParser:
    """Unit tests for PDF parsing functionality."""
    
    @patch('services.parsers.pdf_parser.PyPDF2')
    def test_extract_text_from_pdf(self, mock_pypdf2):
        """Test text extraction from PDF documents."""
        # Mock PDF reader
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Pump Specifications\nFlow Rate: 1000 L/min\nPressure: 50 m"
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        from services.parsers.pdf_parser import PDFParser
        parser = PDFParser()
        
        result = parser.extract_text("mock_pdf_path.pdf")
        
        assert "Pump Specifications" in result
        assert "Flow Rate: 1000 L/min" in result
        assert "Pressure: 50 m" in result
    
    @patch('services.parsers.pdf_parser.PyPDF2')
    def test_extract_product_specs_from_pdf(self, mock_pypdf2):
        """Test extracting product specifications from PDF text."""
        pdf_text = """
        Product Datasheet
        Model: CP-1000
        Flow Rate: 1000 L/min
        Head Pressure: 50 m
        Power Consumption: 5.5 kW
        Material: Stainless Steel
        """
        
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = pdf_text
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        from services.parsers.pdf_parser import PDFParser
        parser = PDFParser()
        
        result = parser.extract_specifications("mock_pdf_path.pdf")
        
        assert "model" in result
        assert "flow_rate" in result
        assert "head_pressure" in result
        assert "power_consumption" in result
        assert result["model"] == "CP-1000"
        assert "1000" in result["flow_rate"]


class TestParserDispatcher:
    """Unit tests for the parser dispatcher that routes to appropriate parsers."""
    
    def test_dispatch_html_parser(self):
        """Test dispatching to HTML parser based on content type."""
        with patch('services.parsers.dispatcher.HTMLParser') as mock_html_parser:
            mock_parser_instance = Mock()
            mock_parser_instance.parse_product_table.return_value = [create_test_product()]
            mock_html_parser.return_value = mock_parser_instance
            
            from services.parsers.dispatcher import ParserDispatcher
            dispatcher = ParserDispatcher()
            
            result = dispatcher.parse_content("<html>content</html>", content_type="text/html")
            
            assert len(result) == 1
            mock_html_parser.assert_called_once()
            mock_parser_instance.parse_product_table.assert_called_once()
    
    def test_dispatch_csv_parser(self):
        """Test dispatching to CSV parser based on content type."""
        with patch('services.parsers.dispatcher.CSVParser') as mock_csv_parser:
            mock_parser_instance = Mock()
            mock_parser_instance.parse_products.return_value = [create_test_product()]
            mock_csv_parser.return_value = mock_parser_instance
            
            from services.parsers.dispatcher import ParserDispatcher
            dispatcher = ParserDispatcher()
            
            result = dispatcher.parse_content("name,type\nPump A,pump", content_type="text/csv")
            
            assert len(result) == 1
            mock_csv_parser.assert_called_once()
    
    def test_dispatch_json_parser(self):
        """Test dispatching to JSON parser based on content type."""
        with patch('services.parsers.dispatcher.JSONParser') as mock_json_parser:
            mock_parser_instance = Mock()
            mock_parser_instance.parse_api_response.return_value = [create_test_product()]
            mock_json_parser.return_value = mock_parser_instance
            
            from services.parsers.dispatcher import ParserDispatcher
            dispatcher = ParserDispatcher()
            
            json_content = '{"products": [{"name": "Test Product"}]}'
            result = dispatcher.parse_content(json_content, content_type="application/json")
            
            assert len(result) == 1
            mock_json_parser.assert_called_once()
    
    def test_dispatch_unsupported_content_type(self):
        """Test handling of unsupported content types."""
        from services.parsers.dispatcher import ParserDispatcher
        dispatcher = ParserDispatcher()
        
        with pytest.raises(ValueError, match="Unsupported content type"):
            dispatcher.parse_content("content", content_type="application/unknown")
    
    def test_auto_detect_content_type(self):
        """Test automatic content type detection."""
        with patch('services.parsers.dispatcher.HTMLParser') as mock_html_parser:
            mock_parser_instance = Mock()
            mock_parser_instance.parse_product_table.return_value = []
            mock_html_parser.return_value = mock_parser_instance
            
            from services.parsers.dispatcher import ParserDispatcher
            dispatcher = ParserDispatcher()
            
            # HTML content without explicit content type
            html_content = "<html><body><table></table></body></html>"
            result = dispatcher.parse_content(html_content)
            
            mock_html_parser.assert_called_once()


class TestParserUtilities:
    """Unit tests for parser utility functions."""
    
    def test_normalize_product_data(self):
        """Test product data normalization."""
        raw_data = {
            "Name": "  Pump Model A  ",
            "Flow Rate (L/min)": "1,000",
            "Head Pressure (m)": "50.0",
            "Price ($)": "$5,000.00",
            "Material": "STAINLESS STEEL"
        }
        
        from services.parsers.utils import normalize_product_data
        
        result = normalize_product_data(raw_data)
        
        assert result["name"] == "Pump Model A"
        assert result["flow_rate_lpm"] == 1000
        assert result["head_pressure_m"] == 50.0
        assert result["price_usd"] == 5000.0
        assert result["material"] == "stainless_steel"
    
    def test_extract_numeric_value(self):
        """Test numeric value extraction from strings."""
        from services.parsers.utils import extract_numeric_value
        
        assert extract_numeric_value("1,000 L/min") == 1000
        assert extract_numeric_value("$5,000.00") == 5000.0
        assert extract_numeric_value("50.5 m") == 50.5
        assert extract_numeric_value("N/A") is None
        assert extract_numeric_value("") is None
    
    def test_standardize_units(self):
        """Test unit standardization."""
        from services.parsers.utils import standardize_units
        
        assert standardize_units("1000 L/min") == {"value": 1000, "unit": "lpm"}
        assert standardize_units("50 meters") == {"value": 50, "unit": "m"}
        assert standardize_units("5.5 kW") == {"value": 5.5, "unit": "kw"}
        assert standardize_units("2 inches") == {"value": 50.8, "unit": "mm"}  # Converted to mm
    
    def test_validate_parsed_data(self):
        """Test validation of parsed product data."""
        from services.parsers.utils import validate_parsed_data
        
        valid_data = {
            "name": "Test Pump",
            "product_type": "pump",
            "flow_rate_lpm": 1000,
            "price_usd": 5000
        }
        
        invalid_data = {
            "name": "",  # Empty name
            "product_type": "invalid_type",
            "flow_rate_lpm": -100,  # Negative flow rate
            "price_usd": "invalid"  # Non-numeric price
        }
        
        assert validate_parsed_data(valid_data) is True
        assert validate_parsed_data(invalid_data) is False
    
    def test_clean_html_text(self):
        """Test HTML text cleaning utility."""
        from services.parsers.utils import clean_html_text
        
        html_text = "  <b>Pump Model A</b>\n\t<br>Flow: 1000 L/min  "
        cleaned = clean_html_text(html_text)
        
        assert cleaned == "Pump Model A Flow: 1000 L/min"
        assert "<b>" not in cleaned
        assert "<br>" not in cleaned
        assert not cleaned.startswith(" ")
        assert not cleaned.endswith(" ")


class TestParserErrorHandling:
    """Unit tests for parser error handling and edge cases."""
    
    def test_handle_empty_content(self):
        """Test handling of empty content."""
        from services.parsers.dispatcher import ParserDispatcher
        dispatcher = ParserDispatcher()
        
        result = dispatcher.parse_content("", content_type="text/html")
        assert result == []
        
        result = dispatcher.parse_content(None, content_type="text/csv")
        assert result == []
    
    def test_handle_corrupted_data(self):
        """Test handling of corrupted or malformed data."""
        corrupted_csv = "name,type\nPump A,pump\nIncomplete row"
        
        with patch('pandas.read_csv') as mock_read_csv:
            # Simulate pandas handling corrupted CSV
            mock_read_csv.side_effect = pd.errors.ParserError("Error tokenizing data")
            
            from services.parsers.csv_parser import CSVParser
            parser = CSVParser()
            
            with pytest.raises(ValueError, match="Failed to parse CSV"):
                parser.parse_products(StringIO(corrupted_csv))
    
    def test_handle_encoding_issues(self):
        """Test handling of encoding issues in text content."""
        # Simulate content with encoding issues
        content_with_encoding_issues = "Pump Modèl Â with spëcial chars"
        
        from services.parsers.utils import clean_html_text
        
        # Should handle encoding gracefully
        result = clean_html_text(content_with_encoding_issues)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_parser_timeout_handling(self):
        """Test handling of parser timeouts for large content."""
        # Simulate very large content that might cause timeout
        large_content = "<table>" + "<tr><td>data</td></tr>" * 10000 + "</table>"
        
        with patch('services.parsers.html_parser.BeautifulSoup') as mock_soup:
            # Simulate timeout
            mock_soup.side_effect = TimeoutError("Parser timeout")
            
            from services.parsers.html_parser import HTMLParser
            parser = HTMLParser()
            
            with pytest.raises(TimeoutError):
                parser.parse_product_table(large_content)