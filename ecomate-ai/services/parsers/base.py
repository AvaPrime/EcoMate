"""Base parser class for EcoMate AI parsers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseParser(ABC):
    """Abstract base class for all parsers."""
    
    def __init__(self, name: str):
        """Initialize the parser with a name.
        
        Args:
            name: The name of the parser
        """
        self.name = name
    
    @abstractmethod
    def parse(self, data: Any) -> Dict[str, Any]:
        """Parse the input data and return structured output.
        
        Args:
            data: The input data to parse
            
        Returns:
            Dict containing parsed data
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate the parsed data.
        
        Args:
            data: The parsed data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    def preprocess(self, data: Any) -> Any:
        """Preprocess the input data before parsing.
        
        Args:
            data: The input data to preprocess
            
        Returns:
            Preprocessed data
        """
        return data
    
    def postprocess(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess the parsed data.
        
        Args:
            data: The parsed data to postprocess
            
        Returns:
            Postprocessed data
        """
        return data