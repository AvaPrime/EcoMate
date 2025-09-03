from typing import List, Dict
from .base import BaseParser


class LLMFallbackParser(BaseParser):
    """Fallback parser that uses LLM for parsing when other parsers fail."""
    
    def __init__(self, name: str = "LLMFallbackParser"):
        super().__init__(name)
        self.category = "fallback"
    
    def parse(self, data: str, url: str = "", vendor: str = None) -> Dict[str, List[dict]]:
        """Parse data using LLM as fallback method."""
        # This is a simplified implementation for testing
        # In a real implementation, this would use an LLM API to parse unknown formats
        return {"suppliers": [], "parts": [], "report": {"status": "fallback_used", "rows": 0}}
    
    def validate(self, data: Dict) -> bool:
        """Validate parsed data.
        
        Args:
            data: Parsed data to validate
            
        Returns:
            True if data is valid
        """
        # LLM fallback has minimal validation requirements
        return isinstance(data, dict) and len(data) > 0
    
    def can_parse(self, data: str, url: str = "") -> bool:
        """This parser can handle any data as a fallback."""
        # Always return True as this is the fallback parser
        return True
    
    def get_confidence(self, data: str, url: str = "") -> float:
        """Return confidence score for parsing this data."""
        # Fallback parser has the lowest confidence
        return 0.1