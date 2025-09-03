"""Unit tests for HTML parsing utility functions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Dict, Any, Optional
import re

from src.utils.html_parser import (
    HTMLParser,
    HTMLElement,
    HTMLParseError,
    extract_text,
    extract_links,
    extract_images,
    extract_tables,
    extract_forms,
    clean_html,
    normalize_whitespace,
    remove_scripts_and_styles,
    find_elements_by_class,
    find_elements_by_id,
    find_elements_by_attribute,
    extract_meta_tags,
    parse_price,
    parse_specifications,
    detect_product_info,
    sanitize_html
)
from src.utils.exceptions import ValidationError, ParsingError


class TestHTMLParser:
    """Test cases for HTMLParser class."""
    
    @pytest.fixture
    def html_parser(self):
        """Create an HTMLParser instance for testing."""
        return HTMLParser(
            remove_scripts=True,
            remove_styles=True,
            normalize_whitespace=True
        )
    
    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test page description">
            <script>console.log('test');</script>
            <style>body { margin: 0; }</style>
        </head>
        <body>
            <div class="header">
                <h1 id="main-title">Product Catalog</h1>
                <nav>
                    <a href="/products">Products</a>
                    <a href="/about">About</a>
                </nav>
            </div>
            <main class="content">
                <div class="product" data-id="123">
                    <h2>Water Pump Model XYZ</h2>
                    <img src="/images/pump.jpg" alt="Water Pump">
                    <p class="price">$1,299.99</p>
                    <table class="specifications">
                        <tr><td>Flow Rate</td><td>100 GPM</td></tr>
                        <tr><td>Head</td><td>150 ft</td></tr>
                        <tr><td>Power</td><td>5 HP</td></tr>
                    </table>
                </div>
                <form id="contact-form">
                    <input type="text" name="name" placeholder="Name">
                    <input type="email" name="email" placeholder="Email">
                    <textarea name="message"></textarea>
                    <button type="submit">Submit</button>
                </form>
            </main>
        </body>
        </html>
        """
    
    def test_html_parser_initialization(self, html_parser):
        """Test HTMLParser initialization."""
        assert html_parser.remove_scripts is True
        assert html_parser.remove_styles is True
        assert html_parser.normalize_whitespace is True
    
    def test_parse_valid_html(self, html_parser, sample_html):
        """Test parsing valid HTML content."""
        result = html_parser.parse(sample_html)
        
        assert isinstance(result, BeautifulSoup)
        assert result.title.string == "Test Page"
        assert result.find('h1', id='main-title').string == "Product Catalog"
    
    def test_parse_malformed_html(self, html_parser):
        """Test parsing malformed HTML."""
        malformed_html = "<div><p>Unclosed paragraph<div>Nested incorrectly</p></div>"
        
        result = html_parser.parse(malformed_html)
        
        # BeautifulSoup should handle malformed HTML gracefully
        assert isinstance(result, BeautifulSoup)
        assert result.find('div') is not None
    
    def test_parse_empty_html(self, html_parser):
        """Test parsing empty HTML."""
        result = html_parser.parse("")
        
        assert isinstance(result, BeautifulSoup)
        assert len(result.get_text().strip()) == 0
    
    def test_remove_scripts_and_styles(self, html_parser, sample_html):
        """Test removal of script and style tags."""
        result = html_parser.parse(sample_html)
        
        # Scripts and styles should be removed
        assert result.find('script') is None
        assert result.find('style') is None
    
    def test_preserve_scripts_and_styles(self, sample_html):
        """Test preserving script and style tags when configured."""
        parser = HTMLParser(remove_scripts=False, remove_styles=False)
        result = parser.parse(sample_html)
        
        assert result.find('script') is not None
        assert result.find('style') is not None
    
    def test_extract_text_content(self, html_parser, sample_html):
        """Test text extraction from HTML."""
        result = html_parser.parse(sample_html)
        text = html_parser.extract_text(result)
        
        assert "Product Catalog" in text
        assert "Water Pump Model XYZ" in text
        assert "$1,299.99" in text
        assert "console.log" not in text  # Script content removed
    
    def test_find_elements_by_selector(self, html_parser, sample_html):
        """Test finding elements by CSS selector."""
        result = html_parser.parse(sample_html)
        
        # Find by class
        products = html_parser.find_elements(result, '.product')
        assert len(products) == 1
        assert products[0].get('data-id') == '123'
        
        # Find by ID
        title = html_parser.find_element(result, '#main-title')
        assert title.string == "Product Catalog"
        
        # Find by tag and attribute
        images = html_parser.find_elements(result, 'img[alt="Water Pump"]')
        assert len(images) == 1
        assert images[0].get('src') == '/images/pump.jpg'


class TestHTMLElement:
    """Test cases for HTMLElement wrapper class."""
    
    def test_html_element_creation(self):
        """Test HTMLElement creation from BeautifulSoup tag."""
        html = '<div class="test" id="element">Content</div>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('div')
        
        element = HTMLElement(tag)
        
        assert element.tag_name == 'div'
        assert element.text == 'Content'
        assert element.get_attribute('class') == ['test']
        assert element.get_attribute('id') == 'element'
    
    def test_html_element_children(self):
        """Test HTMLElement children access."""
        html = '<div><p>Paragraph 1</p><p>Paragraph 2</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')
        
        element = HTMLElement(div)
        children = element.children
        
        assert len(children) == 2
        assert all(child.tag_name == 'p' for child in children)
        assert children[0].text == 'Paragraph 1'
        assert children[1].text == 'Paragraph 2'
    
    def test_html_element_parent(self):
        """Test HTMLElement parent access."""
        html = '<div class="parent"><p class="child">Content</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        p = soup.find('p')
        
        element = HTMLElement(p)
        parent = element.parent
        
        assert parent is not None
        assert parent.tag_name == 'div'
        assert parent.get_attribute('class') == ['parent']


class TestTextExtraction:
    """Test cases for text extraction functions."""
    
    def test_extract_text_basic(self):
        """Test basic text extraction."""
        html = '<div><p>Hello <strong>world</strong>!</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        text = extract_text(soup)
        
        assert text.strip() == 'Hello world!'
    
    def test_extract_text_with_whitespace_normalization(self):
        """Test text extraction with whitespace normalization."""
        html = '<div>   Multiple    spaces   and\n\nnewlines   </div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        text = extract_text(soup, normalize_whitespace=True)
        
        assert text.strip() == 'Multiple spaces and newlines'
    
    def test_extract_text_preserve_whitespace(self):
        """Test text extraction preserving whitespace."""
        html = '<div>   Multiple    spaces   </div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        text = extract_text(soup, normalize_whitespace=False)
        
        assert '   Multiple    spaces   ' in text
    
    def test_extract_text_from_specific_elements(self):
        """Test text extraction from specific elements."""
        html = '''
        <div>
            <h1>Title</h1>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
            <span>Span text</span>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract only from paragraphs
        paragraphs = soup.find_all('p')
        text = ' '.join(extract_text(p) for p in paragraphs)
        
        assert 'Paragraph 1 Paragraph 2' in text
        assert 'Title' not in text
        assert 'Span text' not in text


class TestLinkExtraction:
    """Test cases for link extraction functions."""
    
    def test_extract_links_basic(self):
        """Test basic link extraction."""
        html = '''
        <div>
            <a href="/page1">Link 1</a>
            <a href="https://example.com">External Link</a>
            <a href="mailto:test@example.com">Email Link</a>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        links = extract_links(soup)
        
        assert len(links) == 3
        assert any(link['href'] == '/page1' for link in links)
        assert any(link['href'] == 'https://example.com' for link in links)
        assert any(link['href'] == 'mailto:test@example.com' for link in links)
    
    def test_extract_links_with_text(self):
        """Test link extraction including link text."""
        html = '<a href="/products" title="Product Page">View Products</a>'
        soup = BeautifulSoup(html, 'html.parser')
        
        links = extract_links(soup, include_text=True)
        
        assert len(links) == 1
        link = links[0]
        assert link['href'] == '/products'
        assert link['text'] == 'View Products'
        assert link['title'] == 'Product Page'
    
    def test_extract_links_filter_by_domain(self):
        """Test filtering links by domain."""
        html = '''
        <div>
            <a href="/internal">Internal</a>
            <a href="https://example.com/page">Same Domain</a>
            <a href="https://other.com/page">Other Domain</a>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        links = extract_links(soup, base_url='https://example.com', internal_only=True)
        
        # Should include relative and same-domain links
        assert len(links) == 2
        hrefs = [link['href'] for link in links]
        assert 'https://example.com/internal' in hrefs
        assert 'https://example.com/page' in hrefs


class TestImageExtraction:
    """Test cases for image extraction functions."""
    
    def test_extract_images_basic(self):
        """Test basic image extraction."""
        html = '''
        <div>
            <img src="/image1.jpg" alt="Image 1">
            <img src="https://example.com/image2.png" alt="Image 2" width="100">
            <img src="data:image/gif;base64,R0lGOD..." alt="Base64 Image">
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        images = extract_images(soup)
        
        assert len(images) == 3
        assert any(img['src'] == '/image1.jpg' for img in images)
        assert any(img['src'] == 'https://example.com/image2.png' for img in images)
        assert any(img['src'].startswith('data:image/gif') for img in images)
    
    def test_extract_images_with_attributes(self):
        """Test image extraction with all attributes."""
        html = '<img src="/product.jpg" alt="Product Image" width="300" height="200" class="product-img">'
        soup = BeautifulSoup(html, 'html.parser')
        
        images = extract_images(soup, include_attributes=True)
        
        assert len(images) == 1
        img = images[0]
        assert img['src'] == '/product.jpg'
        assert img['alt'] == 'Product Image'
        assert img['width'] == '300'
        assert img['height'] == '200'
        assert img['class'] == ['product-img']
    
    def test_extract_images_filter_by_size(self):
        """Test filtering images by size attributes."""
        html = '''
        <div>
            <img src="/small.jpg" width="50" height="50">
            <img src="/large.jpg" width="500" height="400">
            <img src="/no-size.jpg">
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        large_images = extract_images(soup, min_width=200, min_height=200)
        
        assert len(large_images) == 1
        assert large_images[0]['src'] == '/large.jpg'


class TestTableExtraction:
    """Test cases for table extraction functions."""
    
    def test_extract_tables_basic(self):
        """Test basic table extraction."""
        html = '''
        <table>
            <thead>
                <tr><th>Name</th><th>Value</th></tr>
            </thead>
            <tbody>
                <tr><td>Flow Rate</td><td>100 GPM</td></tr>
                <tr><td>Head</td><td>150 ft</td></tr>
            </tbody>
        </table>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        tables = extract_tables(soup)
        
        assert len(tables) == 1
        table = tables[0]
        assert len(table['headers']) == 2
        assert table['headers'] == ['Name', 'Value']
        assert len(table['rows']) == 2
        assert table['rows'][0] == ['Flow Rate', '100 GPM']
        assert table['rows'][1] == ['Head', '150 ft']
    
    def test_extract_tables_no_headers(self):
        """Test table extraction without headers."""
        html = '''
        <table>
            <tr><td>Row 1 Col 1</td><td>Row 1 Col 2</td></tr>
            <tr><td>Row 2 Col 1</td><td>Row 2 Col 2</td></tr>
        </table>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        tables = extract_tables(soup)
        
        assert len(tables) == 1
        table = tables[0]
        assert table['headers'] == []
        assert len(table['rows']) == 2
    
    def test_extract_tables_with_attributes(self):
        """Test table extraction with attributes."""
        html = '<table class="specifications" id="spec-table"><tr><td>Data</td></tr></table>'
        soup = BeautifulSoup(html, 'html.parser')
        
        tables = extract_tables(soup, include_attributes=True)
        
        assert len(tables) == 1
        table = tables[0]
        assert table['class'] == ['specifications']
        assert table['id'] == 'spec-table'


class TestFormExtraction:
    """Test cases for form extraction functions."""
    
    def test_extract_forms_basic(self):
        """Test basic form extraction."""
        html = '''
        <form action="/submit" method="post">
            <input type="text" name="username" placeholder="Username">
            <input type="password" name="password">
            <select name="category">
                <option value="pumps">Pumps</option>
                <option value="filters">Filters</option>
            </select>
            <textarea name="comments"></textarea>
            <button type="submit">Submit</button>
        </form>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        forms = extract_forms(soup)
        
        assert len(forms) == 1
        form = forms[0]
        assert form['action'] == '/submit'
        assert form['method'] == 'post'
        assert len(form['fields']) == 4  # username, password, category, comments
        
        # Check field details
        username_field = next(f for f in form['fields'] if f['name'] == 'username')
        assert username_field['type'] == 'text'
        assert username_field['placeholder'] == 'Username'
    
    def test_extract_forms_with_validation(self):
        """Test form extraction with validation attributes."""
        html = '''
        <form>
            <input type="email" name="email" required>
            <input type="number" name="quantity" min="1" max="100">
            <input type="text" name="phone" pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}">
        </form>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        forms = extract_forms(soup)
        
        form = forms[0]
        email_field = next(f for f in form['fields'] if f['name'] == 'email')
        quantity_field = next(f for f in form['fields'] if f['name'] == 'quantity')
        phone_field = next(f for f in form['fields'] if f['name'] == 'phone')
        
        assert email_field['required'] is True
        assert quantity_field['min'] == '1'
        assert quantity_field['max'] == '100'
        assert phone_field['pattern'] == '[0-9]{3}-[0-9]{3}-[0-9]{4}'


class TestHTMLCleaning:
    """Test cases for HTML cleaning functions."""
    
    def test_clean_html_basic(self):
        """Test basic HTML cleaning."""
        dirty_html = '''
        <div>
            <script>alert('xss');</script>
            <p>Clean content</p>
            <style>body { display: none; }</style>
            <iframe src="evil.com"></iframe>
        </div>
        '''
        
        clean = clean_html(dirty_html)
        
        assert '<script>' not in clean
        assert '<style>' not in clean
        assert '<iframe>' not in clean
        assert 'Clean content' in clean
    
    def test_remove_scripts_and_styles_function(self):
        """Test script and style removal function."""
        html = '''
        <html>
            <head>
                <script src="script.js"></script>
                <style>body { margin: 0; }</style>
            </head>
            <body>
                <p>Content</p>
                <script>console.log('inline');</script>
            </body>
        </html>
        '''
        
        cleaned = remove_scripts_and_styles(html)
        soup = BeautifulSoup(cleaned, 'html.parser')
        
        assert soup.find('script') is None
        assert soup.find('style') is None
        assert soup.find('p').string == 'Content'
    
    def test_normalize_whitespace_function(self):
        """Test whitespace normalization function."""
        text = "   Multiple   \n\n   spaces   and\ttabs   "
        
        normalized = normalize_whitespace(text)
        
        assert normalized == "Multiple spaces and tabs"
    
    def test_sanitize_html_function(self):
        """Test HTML sanitization function."""
        dangerous_html = '''
        <div onclick="alert('xss')">Content</div>
        <a href="javascript:alert('xss')">Link</a>
        <img src="x" onerror="alert('xss')">
        '''
        
        safe_html = sanitize_html(dangerous_html)
        
        assert 'onclick' not in safe_html
        assert 'javascript:' not in safe_html
        assert 'onerror' not in safe_html
        assert 'Content' in safe_html
        assert 'Link' in safe_html


class TestElementFinding:
    """Test cases for element finding functions."""
    
    def test_find_elements_by_class(self):
        """Test finding elements by class name."""
        html = '''
        <div>
            <p class="highlight">Paragraph 1</p>
            <p class="normal">Paragraph 2</p>
            <span class="highlight small">Span</span>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        elements = find_elements_by_class(soup, 'highlight')
        
        assert len(elements) == 2
        assert elements[0].name == 'p'
        assert elements[1].name == 'span'
    
    def test_find_elements_by_id(self):
        """Test finding elements by ID."""
        html = '''
        <div>
            <h1 id="main-title">Title</h1>
            <p id="description">Description</p>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        title = find_elements_by_id(soup, 'main-title')
        description = find_elements_by_id(soup, 'description')
        
        assert len(title) == 1
        assert title[0].string == 'Title'
        assert len(description) == 1
        assert description[0].string == 'Description'
    
    def test_find_elements_by_attribute(self):
        """Test finding elements by custom attributes."""
        html = '''
        <div>
            <div data-product-id="123">Product A</div>
            <div data-product-id="456">Product B</div>
            <div data-category="pumps">Category</div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        products = find_elements_by_attribute(soup, 'data-product-id')
        category = find_elements_by_attribute(soup, 'data-category', 'pumps')
        
        assert len(products) == 2
        assert len(category) == 1
        assert category[0].string == 'Category'


class TestMetaTagExtraction:
    """Test cases for meta tag extraction."""
    
    def test_extract_meta_tags(self):
        """Test meta tag extraction."""
        html = '''
        <html>
        <head>
            <meta name="description" content="Product catalog page">
            <meta name="keywords" content="pumps, filters, water treatment">
            <meta property="og:title" content="EcoMate Products">
            <meta property="og:image" content="/images/logo.png">
            <meta charset="utf-8">
        </head>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        meta_tags = extract_meta_tags(soup)
        
        assert 'description' in meta_tags
        assert meta_tags['description'] == 'Product catalog page'
        assert 'keywords' in meta_tags
        assert 'og:title' in meta_tags
        assert meta_tags['og:title'] == 'EcoMate Products'
        assert 'charset' in meta_tags


class TestProductInfoDetection:
    """Test cases for product information detection."""
    
    def test_parse_price(self):
        """Test price parsing from text."""
        price_texts = [
            "$1,299.99",
            "Price: $2,500.00",
            "€1.500,50",
            "£999.99",
            "1299.99 USD",
            "Starting at $899"
        ]
        
        for text in price_texts:
            price = parse_price(text)
            assert price is not None
            assert isinstance(price, (int, float))
            assert price > 0
    
    def test_parse_price_invalid(self):
        """Test price parsing with invalid input."""
        invalid_texts = [
            "No price here",
            "Free shipping",
            "Contact for pricing",
            ""
        ]
        
        for text in invalid_texts:
            price = parse_price(text)
            assert price is None
    
    def test_parse_specifications(self):
        """Test specification parsing from HTML table."""
        html = '''
        <table class="specifications">
            <tr><td>Flow Rate</td><td>100 GPM</td></tr>
            <tr><td>Head</td><td>150 ft</td></tr>
            <tr><td>Power</td><td>5 HP</td></tr>
            <tr><td>Efficiency</td><td>85%</td></tr>
        </table>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        
        specs = parse_specifications(table)
        
        assert 'Flow Rate' in specs
        assert specs['Flow Rate'] == '100 GPM'
        assert 'Head' in specs
        assert specs['Head'] == '150 ft'
        assert 'Power' in specs
        assert specs['Power'] == '5 HP'
    
    def test_detect_product_info(self):
        """Test comprehensive product information detection."""
        html = '''
        <div class="product">
            <h2>Centrifugal Water Pump Model CP-100</h2>
            <div class="price">$1,299.99</div>
            <img src="/images/cp100.jpg" alt="CP-100 Pump">
            <div class="description">
                High-efficiency centrifugal pump for industrial applications.
            </div>
            <table class="specs">
                <tr><td>Flow Rate</td><td>100 GPM</td></tr>
                <tr><td>Head</td><td>150 ft</td></tr>
                <tr><td>Power</td><td>5 HP</td></tr>
            </table>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        product_info = detect_product_info(soup)
        
        assert 'name' in product_info
        assert 'Centrifugal Water Pump' in product_info['name']
        assert 'price' in product_info
        assert product_info['price'] == 1299.99
        assert 'specifications' in product_info
        assert 'Flow Rate' in product_info['specifications']
        assert 'images' in product_info
        assert len(product_info['images']) == 1


class TestErrorHandling:
    """Test cases for error handling in HTML parsing."""
    
    def test_parse_invalid_html_encoding(self):
        """Test handling of invalid HTML encoding."""
        # This would test handling of different encodings
        # Implementation depends on specific encoding requirements
        pass
    
    def test_parse_extremely_large_html(self):
        """Test handling of extremely large HTML documents."""
        # Generate large HTML content
        large_html = "<div>" + "<p>Content</p>" * 10000 + "</div>"
        
        parser = HTMLParser()
        result = parser.parse(large_html)
        
        # Should handle large documents without crashing
        assert isinstance(result, BeautifulSoup)
    
    def test_parse_deeply_nested_html(self):
        """Test handling of deeply nested HTML structures."""
        # Create deeply nested structure
        nested_html = "<div>" * 100 + "Content" + "</div>" * 100
        
        parser = HTMLParser()
        result = parser.parse(nested_html)
        
        assert isinstance(result, BeautifulSoup)
        assert "Content" in result.get_text()


@pytest.mark.parametrize("html_input,expected_tag_count", [
    ("<p>Single paragraph</p>", 1),
    ("<div><p>Para 1</p><p>Para 2</p></div>", 3),
    ("<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>", 4),
    ("", 0),
])
def test_tag_counting(html_input, expected_tag_count):
    """Parametrized test for counting HTML tags."""
    soup = BeautifulSoup(html_input, 'html.parser')
    tags = soup.find_all()
    
    assert len(tags) == expected_tag_count


@pytest.mark.parametrize("price_text,expected_value", [
    ("$1,299.99", 1299.99),
    ("€1.500,50", 1500.50),
    ("£999.99", 999.99),
    ("1299.99 USD", 1299.99),
    ("Price: $2,500.00", 2500.00),
    ("Starting at $899", 899.00),
])
def test_price_parsing_parametrized(price_text, expected_value):
    """Parametrized test for price parsing."""
    parsed_price = parse_price(price_text)
    
    assert parsed_price is not None
    assert abs(parsed_price - expected_value) < 0.01  # Allow for floating point precision


class TestPerformanceAndMemory:
    """Test cases for performance and memory usage."""
    
    @pytest.mark.slow
    def test_large_document_parsing_performance(self):
        """Test parsing performance with large documents."""
        import time
        
        # Generate large HTML document
        large_html = "<html><body>"
        for i in range(1000):
            large_html += f"<div class='item-{i}'><h3>Item {i}</h3><p>Description for item {i}</p></div>"
        large_html += "</body></html>"
        
        parser = HTMLParser()
        
        start_time = time.time()
        result = parser.parse(large_html)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Should parse within reasonable time (adjust threshold as needed)
        assert parse_time < 5.0  # 5 seconds max
        assert isinstance(result, BeautifulSoup)
    
    def test_memory_usage_with_multiple_parses(self):
        """Test memory usage with multiple parsing operations."""
        # This would test memory usage patterns
        # Implementation depends on specific memory monitoring requirements
        pass