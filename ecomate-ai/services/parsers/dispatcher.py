from typing import List, Dict, Optional
from urllib.parse import urlparse
from .pumps import parse_pump_table, PumpParser
from .uv import parse_uv_table, UVReactorParser
from .llm_fallback import LLMFallbackParser
from .base import BaseParser
from ..utils.exceptions import ParserError

# Map domain keywords or categories to parser functions
PARSER_MAP = {
    "pump": parse_pump_table,
    "uv": parse_uv_table,
}

# Option A: decide by category hint

def parse_by_category(category: str, rows: List[List[str]], url: str, vendor: Optional[str] = None) -> Optional[Dict]:
    for key, fn in PARSER_MAP.items():
        if key in (category or '').lower():
            return fn(rows, url, vendor)
    return None

# Option B: decide by domain keyword (simple heuristic)
DOMAIN_HINTS = {
    "grundfos.com": "Grundfos",
    "xylem.com": "Xylem",
    "trojanuv.com": "Trojan Technologies",
    "pentair.com": "Pentair",
    "wilo.com": "Wilo",
}

def parse_by_domain(url: str, rows: List[List[str]]) -> Optional[Dict]:
    host = urlparse(url).netloc.lower()
    for k, cat in DOMAIN_HINTS.items():
        if k in host:
            return parse_by_category(cat, rows, url, vendor=host)
    return None


class ParserDispatcher:
    """Dispatcher class for routing parsing requests to appropriate parsers."""
    
    def __init__(self):
        """Initialize the parser dispatcher."""
        self.parser_map = PARSER_MAP
        self.domain_hints = DOMAIN_HINTS
        self._parser_cache = {}  # Cache for parser instances
    
    def parse_by_category(self, category: str, rows: List[List[str]], url: str, vendor: Optional[str] = None) -> Optional[Dict]:
        """Parse data by category.
        
        Args:
            category: The category hint for parsing
            rows: The data rows to parse
            url: The source URL
            vendor: Optional vendor name
            
        Returns:
            Parsed data dictionary or None
        """
        return parse_by_category(category, rows, url, vendor)
    
    def parse_by_domain(self, url: str, rows: List[List[str]]) -> Optional[Dict]:
        """Parse data by domain.
        
        Args:
            url: The source URL
            rows: The data rows to parse
            
        Returns:
            Parsed data dictionary or None
        """
        return parse_by_domain(url, rows)
    
    def get_available_parsers(self) -> List[str]:
        """Get list of available parser categories.
        
        Returns:
            List of available parser category names
        """
        return list(self.parser_map.keys())
    
    def detect_supplier(self, url: str) -> str:
        """Detect supplier from URL.
        
        Args:
            url: The URL to analyze
            
        Returns:
            Detected supplier name or 'Unknown'
        """
        url_lower = url.lower()
        for domain, vendor in self.domain_hints.items():
            if domain in url_lower:
                return vendor
        return "Unknown"
    
    def detect_product_type(self, url: str) -> str:
        """Detect product type from URL.
        
        Args:
            url: The URL to analyze
            
        Returns:
            Detected product type
        """
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in ["pump", "centrifugal", "submersible"]):
            return "pumps"
        elif any(keyword in url_lower for keyword in ["uv", "ultraviolet", "reactor"]):
            return "uv"
        else:
            return "general"
    
    def detect_product_type_from_html(self, html_content: str) -> str:
        """Detect product type from HTML content.
        
        Args:
            html_content: The HTML content to analyze
            
        Returns:
            Detected product type
        """
        if html_content is None:
            return "general"
        
        html_lower = html_content.lower()
        if any(keyword in html_lower for keyword in ["pump", "centrifugal", "submersible"]):
            return "pumps"
        elif any(keyword in html_lower for keyword in ["uv", "ultraviolet", "reactor"]):
            return "uv"
        else:
            return "general"
    
    def get_parser(self, supplier: str, product_type: str):
        """Get parser instance for a supplier and product type.
        
        Args:
            supplier: The supplier name
            product_type: The product type (pumps, uv, etc.)
            
        Returns:
            Parser instance
        """
        cache_key = f"{supplier}_{product_type}"
        
        # Return cached parser if available
        if cache_key in self._parser_cache:
            return self._parser_cache[cache_key]
        
        # Create appropriate parser based on supplier and product type
        if product_type == "pumps":
            if supplier in ["Grundfos", "Xylem", "Pentair", "Wilo"]:
                parser = PumpParser(f"PumpParser_{supplier}")
            else:
                parser = LLMFallbackParser(f"LLMFallbackParser_{supplier}")
        elif product_type == "uv":
            if supplier in ["Trojan Technologies", "Xylem", "Atlantium"]:
                parser = UVReactorParser(f"UVReactorParser_{supplier}")
            else:
                parser = LLMFallbackParser(f"LLMFallbackParser_{supplier}")
        else:
            parser = LLMFallbackParser(f"LLMFallbackParser_{supplier}")
        
        # Cache the parser
        self._parser_cache[cache_key] = parser
        return parser
    
    def dispatch(self, html_content: str, url: str = "") -> List[Dict]:
        """Dispatch parsing request to appropriate parser.
        
        Args:
            html_content: The HTML content to parse
            url: Source URL
            
        Returns:
            List of parsed data dictionaries
        """
        # Handle error cases
        if html_content is None:
            raise ParserError("HTML content cannot be None", "dispatcher", url)
        
        if not html_content.strip():
            return []
        
        # Validate URL
        if url and not (url.startswith('http://') or url.startswith('https://')):
            raise ParserError("Invalid URL format", "dispatcher", url)
        
        # Detect supplier and product type
        supplier = self.detect_supplier(url)
        # Try to detect product type from URL first, then from HTML content
        product_type = self.detect_product_type(url)
        if product_type == "general":
            product_type = self.detect_product_type_from_html(html_content)
        
        # Get appropriate parser
        parser = self.get_parser(supplier, product_type)
        
        # Parse the content
        try:
            results = parser.parse(html_content, url)
            return results if isinstance(results, list) else [results]
        except Exception as e:
            raise ParserError(f"Parsing failed: {str(e)}", "dispatcher", url)
    
    def calculate_confidence(self, url: str, supplier: str, product_type: str) -> float:
        """Calculate confidence score for parsing.
        
        Args:
            url: Source URL
            supplier: Detected supplier
            product_type: Detected product type
            
        Returns:
            Confidence score between 0 and 1
        """
        # Simple confidence calculation based on supplier and product type
        score = 0.1  # Base score
        
        # Increase confidence if we can detect product type
        if product_type != "general":
            score += 0.4
        
        # Increase confidence if we can detect supplier
        if supplier != "Unknown":
            score += 0.4
        
        # Extra confidence for known supplier-product combinations
        known_combinations = {
            ("Grundfos", "pumps"): 0.1,
            ("Xylem", "pumps"): 0.1,
            ("Trojan Technologies", "uv"): 0.1,
            ("Pentair", "pumps"): 0.1,
            ("Wilo", "pumps"): 0.1,
        }
        
        if (supplier, product_type) in known_combinations:
            score += known_combinations[(supplier, product_type)]
        
        return min(score, 1.0)
    
    def update_config(self, config: Dict):
        """Update parser configuration.
        
        Args:
            config: Configuration dictionary
        """
        if "parser_map" in config:
            self.parser_map.update(config["parser_map"])
        if "domain_hints" in config:
            self.domain_hints.update(config["domain_hints"])
        if "suppliers" in config:
            self.domain_hints.update(config["suppliers"])
        if "product_types" in config:
            # Handle product type mappings if needed
            pass