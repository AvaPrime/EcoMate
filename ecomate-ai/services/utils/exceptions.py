"""Custom exceptions for the EcoMate AI services."""


class ParserError(Exception):
    """Exception raised when parsing fails."""
    
    def __init__(self, message: str, parser_type: str = None, url: str = None):
        self.message = message
        self.parser_type = parser_type
        self.url = url
        super().__init__(self.message)
    
    def __str__(self):
        parts = [self.message]
        if self.parser_type:
            parts.append(f"Parser: {self.parser_type}")
        if self.url:
            parts.append(f"URL: {self.url}")
        return " | ".join(parts)


class ValidationError(Exception):
    """Exception raised when data validation fails."""
    pass


class ConfigurationError(Exception):
    """Exception raised when configuration is invalid."""
    pass


class APIError(Exception):
    """Exception raised when API calls fail."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)
    
    def __str__(self):
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        return " | ".join(parts)