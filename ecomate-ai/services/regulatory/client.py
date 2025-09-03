"""Regulatory client for interacting with standards body APIs."""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlencode

import aiohttp
import httpx
from bs4 import BeautifulSoup
from pydantic import ValidationError

from .models import (
    StandardsBody,
    RegulatoryStandard,
    StandardsUpdate,
    ComplianceStatus,
    UpdateType,
    StandardCategory,
    AlertSeverity,
    RegulatoryAlert
)

logger = logging.getLogger(__name__)


class RegulatoryAPIError(Exception):
    """Custom exception for regulatory API errors."""
    pass


class RegulatoryClient:
    """Client for interacting with various regulatory standards body APIs."""
    
    def __init__(
        self,
        api_keys: Dict[str, str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 1800
    ):
        """Initialize the regulatory client.
        
        Args:
            api_keys: Dictionary of API keys for different standards bodies
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            cache_ttl: Cache time-to-live in seconds
        """
        self.api_keys = api_keys or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._session = None
        
        # API endpoints for different standards bodies
        self.endpoints = {
            StandardsBody.SANS: "https://www.sans.org.za/api/v1",
            StandardsBody.ISO: "https://www.iso.org/api/v1",
            StandardsBody.EPA: "https://www.epa.gov/api/v1",
            StandardsBody.OSHA: "https://www.osha.gov/api/v1",
            StandardsBody.ANSI: "https://webstore.ansi.org/api/v1",
            StandardsBody.ASTM: "https://www.astm.org/api/v1",
            StandardsBody.IEC: "https://webstore.iec.ch/api/v1",
            StandardsBody.IEEE: "https://standards.ieee.org/api/v1"
        }
        
        # Headers for different APIs
        self.headers = {
            "User-Agent": "EcoMate-Regulatory-Monitor/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    def _get_cache_key(self, method: str, url: str, params: Dict = None) -> str:
        """Generate cache key for request."""
        key_parts = [method, url]
        if params:
            key_parts.append(urlencode(sorted(params.items())))
        return ":".join(key_parts)
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid."""
        if not cache_entry:
            return False
        return (datetime.utcnow() - cache_entry["timestamp"]).seconds < self.cache_ttl
    
    async def _make_request(
        self,
        method: str,
        url: str,
        params: Dict = None,
        data: Dict = None,
        headers: Dict = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic and caching."""
        cache_key = self._get_cache_key(method, url, params)
        
        # Check cache first for GET requests
        if method.upper() == "GET" and cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.debug(f"Cache hit for {url}")
                return cache_entry["data"]
        
        # Prepare headers
        request_headers = {**self.headers}
        if headers:
            request_headers.update(headers)
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                if not self._session:
                    self._session = aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                        headers=request_headers
                    )
                
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    json=data,
                    headers=request_headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Cache successful GET requests
                        if method.upper() == "GET":
                            self._cache[cache_key] = {
                                "data": result,
                                "timestamp": datetime.utcnow()
                            }
                        
                        return result
                    elif response.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_text = await response.text()
                        raise RegulatoryAPIError(
                            f"API request failed with status {response.status}: {error_text}"
                        )
            
            except aiohttp.ClientError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
        
        raise RegulatoryAPIError(f"Request failed after {self.max_retries} attempts: {last_exception}")
    
    def _get_api_headers(self, body: StandardsBody) -> Dict[str, str]:
        """Get API-specific headers including authentication."""
        headers = {}
        
        if body.value in self.api_keys:
            api_key = self.api_keys[body.value]
            
            # Different authentication methods for different APIs
            if body in [StandardsBody.ISO, StandardsBody.ANSI, StandardsBody.ASTM]:
                headers["Authorization"] = f"Bearer {api_key}"
            elif body in [StandardsBody.IEC, StandardsBody.IEEE]:
                headers["X-API-Key"] = api_key
            else:
                headers["Authorization"] = f"ApiKey {api_key}"
        
        return headers
    
    async def get_standard(self, body: StandardsBody, standard_id: str) -> Optional[RegulatoryStandard]:
        """Get detailed information about a specific standard.
        
        Args:
            body: Standards body
            standard_id: Standard identifier
            
        Returns:
            RegulatoryStandard object or None if not found
        """
        try:
            base_url = self.endpoints.get(body)
            if not base_url:
                raise RegulatoryAPIError(f"No API endpoint configured for {body.value}")
            
            url = urljoin(base_url, f"standards/{standard_id}")
            headers = self._get_api_headers(body)
            
            response = await self._make_request("GET", url, headers=headers)
            
            # Map API response to our standard model
            standard_data = self._map_standard_response(body, response)
            return RegulatoryStandard(**standard_data)
            
        except (ValidationError, KeyError) as e:
            logger.error(f"Error parsing standard data for {standard_id}: {e}")
            return None
        except RegulatoryAPIError as e:
            logger.error(f"API error getting standard {standard_id}: {e}")
            return None
    
    async def search_standards(
        self,
        body: StandardsBody,
        query: str = None,
        category: StandardCategory = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RegulatoryStandard]:
        """Search for standards.
        
        Args:
            body: Standards body
            query: Search query
            category: Standard category filter
            limit: Maximum results to return
            offset: Result offset
            
        Returns:
            List of RegulatoryStandard objects
        """
        try:
            base_url = self.endpoints.get(body)
            if not base_url:
                raise RegulatoryAPIError(f"No API endpoint configured for {body.value}")
            
            url = urljoin(base_url, "standards/search")
            headers = self._get_api_headers(body)
            
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if query:
                params["q"] = query
            if category:
                params["category"] = category.value
            
            response = await self._make_request("GET", url, params=params, headers=headers)
            
            standards = []
            for item in response.get("results", []):
                try:
                    standard_data = self._map_standard_response(body, item)
                    standards.append(RegulatoryStandard(**standard_data))
                except (ValidationError, KeyError) as e:
                    logger.warning(f"Skipping invalid standard data: {e}")
                    continue
            
            return standards
            
        except RegulatoryAPIError as e:
            logger.error(f"API error searching standards: {e}")
            return []
    
    async def get_standards_updates(
        self,
        body: StandardsBody,
        since: date = None,
        limit: int = 100
    ) -> List[StandardsUpdate]:
        """Get recent standards updates.
        
        Args:
            body: Standards body
            since: Get updates since this date
            limit: Maximum results to return
            
        Returns:
            List of StandardsUpdate objects
        """
        try:
            base_url = self.endpoints.get(body)
            if not base_url:
                raise RegulatoryAPIError(f"No API endpoint configured for {body.value}")
            
            url = urljoin(base_url, "standards/updates")
            headers = self._get_api_headers(body)
            
            params = {"limit": limit}
            if since:
                params["since"] = since.isoformat()
            
            response = await self._make_request("GET", url, params=params, headers=headers)
            
            updates = []
            for item in response.get("results", []):
                try:
                    update_data = self._map_update_response(body, item)
                    updates.append(StandardsUpdate(**update_data))
                except (ValidationError, KeyError) as e:
                    logger.warning(f"Skipping invalid update data: {e}")
                    continue
            
            return updates
            
        except RegulatoryAPIError as e:
            logger.error(f"API error getting standards updates: {e}")
            return []
    
    async def get_alerts(
        self,
        body: StandardsBody = None,
        severity: AlertSeverity = None,
        since: date = None,
        limit: int = 100
    ) -> List[RegulatoryAlert]:
        """Get regulatory alerts.
        
        Args:
            body: Standards body filter
            severity: Alert severity filter
            since: Get alerts since this date
            limit: Maximum results to return
            
        Returns:
            List of RegulatoryAlert objects
        """
        alerts = []
        
        # If no specific body requested, get alerts from all bodies
        bodies_to_check = [body] if body else list(StandardsBody)
        
        for standards_body in bodies_to_check:
            try:
                base_url = self.endpoints.get(standards_body)
                if not base_url:
                    continue
                
                url = urljoin(base_url, "alerts")
                headers = self._get_api_headers(standards_body)
                
                params = {"limit": limit}
                if severity:
                    params["severity"] = severity.value
                if since:
                    params["since"] = since.isoformat()
                
                response = await self._make_request("GET", url, params=params, headers=headers)
                
                for item in response.get("results", []):
                    try:
                        alert_data = self._map_alert_response(standards_body, item)
                        alerts.append(RegulatoryAlert(**alert_data))
                    except (ValidationError, KeyError) as e:
                        logger.warning(f"Skipping invalid alert data: {e}")
                        continue
                        
            except RegulatoryAPIError as e:
                logger.error(f"API error getting alerts from {standards_body.value}: {e}")
                continue
        
        return alerts
    
    def _map_standard_response(self, body: StandardsBody, data: Dict) -> Dict[str, Any]:
        """Map API response to standard model format."""
        # Base mapping - different APIs may have different field names
        mapped = {
            "id": data.get("id") or data.get("standard_id") or data.get("number"),
            "title": data.get("title") or data.get("name"),
            "body": body,
            "category": self._map_category(data.get("category") or data.get("type")),
            "number": data.get("number") or data.get("standard_number") or data.get("id"),
            "version": data.get("version") or data.get("edition") or "1.0",
            "publication_date": self._parse_date(data.get("publication_date") or data.get("published")),
            "effective_date": self._parse_date(data.get("effective_date")),
            "review_date": self._parse_date(data.get("review_date")),
            "status": data.get("status") or "active",
            "abstract": data.get("abstract") or data.get("summary"),
            "scope": data.get("scope"),
            "keywords": data.get("keywords") or [],
            "related_standards": data.get("related") or [],
            "supersedes": data.get("supersedes"),
            "superseded_by": data.get("superseded_by"),
            "price": data.get("price"),
            "currency": data.get("currency") or "USD",
            "pages": data.get("pages"),
            "language": data.get("language") or "en",
            "url": data.get("url") or data.get("link"),
            "metadata": data.get("metadata") or {}
        }
        
        # Remove None values
        return {k: v for k, v in mapped.items() if v is not None}
    
    def _map_update_response(self, body: StandardsBody, data: Dict) -> Dict[str, Any]:
        """Map API response to update model format."""
        mapped = {
            "id": data.get("id") or f"{body.value}_{data.get('standard_id')}_{data.get('version')}",
            "standard_id": data.get("standard_id"),
            "update_type": self._map_update_type(data.get("type") or data.get("update_type")),
            "title": data.get("title") or data.get("name"),
            "description": data.get("description") or data.get("summary"),
            "publication_date": self._parse_date(data.get("publication_date") or data.get("date")),
            "effective_date": self._parse_date(data.get("effective_date")),
            "changes": data.get("changes") or [],
            "impact_assessment": data.get("impact") or data.get("impact_assessment"),
            "transition_period": data.get("transition_period"),
            "previous_version": data.get("previous_version"),
            "new_version": data.get("new_version") or data.get("version"),
            "url": data.get("url") or data.get("link"),
            "documents": data.get("documents") or [],
            "metadata": data.get("metadata") or {}
        }
        
        return {k: v for k, v in mapped.items() if v is not None}
    
    def _map_alert_response(self, body: StandardsBody, data: Dict) -> Dict[str, Any]:
        """Map API response to alert model format."""
        mapped = {
            "id": data.get("id") or f"{body.value}_{data.get('alert_id')}",
            "title": data.get("title") or data.get("subject"),
            "message": data.get("message") or data.get("description"),
            "severity": self._map_severity(data.get("severity") or data.get("priority")),
            "body": body,
            "standard_id": data.get("standard_id"),
            "alert_type": data.get("type") or data.get("alert_type") or "general",
            "created_at": self._parse_datetime(data.get("created_at") or data.get("timestamp")),
            "effective_date": self._parse_date(data.get("effective_date")),
            "expiry_date": self._parse_date(data.get("expiry_date")),
            "affected_entities": data.get("affected_entities") or [],
            "action_required": data.get("action_required", False),
            "action_deadline": self._parse_date(data.get("action_deadline")),
            "url": data.get("url") or data.get("link"),
            "acknowledged": data.get("acknowledged", False),
            "acknowledged_by": data.get("acknowledged_by"),
            "acknowledged_at": self._parse_datetime(data.get("acknowledged_at")),
            "metadata": data.get("metadata") or {}
        }
        
        return {k: v for k, v in mapped.items() if v is not None}
    
    def _map_category(self, category: str) -> StandardCategory:
        """Map API category to our enum."""
        if not category:
            return StandardCategory.TECHNICAL
        
        category_lower = category.lower()
        if "environment" in category_lower:
            return StandardCategory.ENVIRONMENTAL
        elif "safety" in category_lower:
            return StandardCategory.SAFETY
        elif "quality" in category_lower:
            return StandardCategory.QUALITY
        elif "security" in category_lower:
            return StandardCategory.SECURITY
        elif "management" in category_lower:
            return StandardCategory.MANAGEMENT
        elif "process" in category_lower:
            return StandardCategory.PROCESS
        elif "product" in category_lower:
            return StandardCategory.PRODUCT
        else:
            return StandardCategory.TECHNICAL
    
    def _map_update_type(self, update_type: str) -> UpdateType:
        """Map API update type to our enum."""
        if not update_type:
            return UpdateType.REVISION
        
        type_lower = update_type.lower()
        if "new" in type_lower:
            return UpdateType.NEW_STANDARD
        elif "amendment" in type_lower:
            return UpdateType.AMENDMENT
        elif "withdrawal" in type_lower or "withdraw" in type_lower:
            return UpdateType.WITHDRAWAL
        elif "confirmation" in type_lower or "confirm" in type_lower:
            return UpdateType.CONFIRMATION
        elif "correction" in type_lower or "corrigendum" in type_lower:
            return UpdateType.CORRECTION
        else:
            return UpdateType.REVISION
    
    def _map_severity(self, severity: str) -> AlertSeverity:
        """Map API severity to our enum."""
        if not severity:
            return AlertSeverity.MEDIUM
        
        severity_lower = severity.lower()
        if severity_lower in ["critical", "urgent", "high"]:
            return AlertSeverity.CRITICAL if "critical" in severity_lower else AlertSeverity.HIGH
        elif severity_lower in ["medium", "normal", "moderate"]:
            return AlertSeverity.MEDIUM
        elif severity_lower in ["low", "info", "information"]:
            return AlertSeverity.LOW
        else:
            return AlertSeverity.MEDIUM
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            # If all formats fail, try parsing as ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            
        except (ValueError, TypeError):
            logger.warning(f"Could not parse date: {date_str}")
            return None
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not datetime_str:
            return None
        
        try:
            # Try different datetime formats
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"]:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, try parsing as ISO format
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
        except (ValueError, TypeError):
            logger.warning(f"Could not parse datetime: {datetime_str}")
            return None
    
    async def health_check(self, body: StandardsBody) -> Dict[str, Any]:
        """Check API health for a standards body.
        
        Args:
            body: Standards body to check
            
        Returns:
            Health check results
        """
        try:
            base_url = self.endpoints.get(body)
            if not base_url:
                return {
                    "status": "error",
                    "message": f"No API endpoint configured for {body.value}"
                }
            
            url = urljoin(base_url, "health")
            headers = self._get_api_headers(body)
            
            start_time = datetime.utcnow()
            response = await self._make_request("GET", url, headers=headers)
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "body": body.value,
                "response_time": response_time,
                "timestamp": end_time.isoformat(),
                "api_version": response.get("version"),
                "features": response.get("features", [])
            }
            
        except RegulatoryAPIError as e:
            return {
                "status": "error",
                "body": body.value,
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def clear_cache(self):
        """Clear the request cache."""
        self._cache.clear()
        logger.info("Request cache cleared")