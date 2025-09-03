# API Troubleshooting Guide

This guide helps developers diagnose and resolve common issues when integrating with the EcoMate API.

## Common Issues

### Authentication Problems

#### Issue: 401 Unauthorized Error

**Symptoms:**
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired authentication token"
}
```

**Possible Causes:**
1. Missing or malformed Authorization header
2. Expired access token
3. Invalid API key
4. Token not properly formatted

**Solutions:**

1. **Check Authorization Header Format:**
   ```bash
   # Correct format for Bearer token
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   
   # Correct format for API Key
   Authorization: ApiKey your-api-key-here
   ```

2. **Refresh Expired Token:**
   ```python
   import requests
   
   # Refresh token request
   response = requests.post('https://api.ecomate.com/v1/auth/refresh', {
       'refresh_token': 'your-refresh-token'
   })
   
   if response.status_code == 200:
       new_token = response.json()['access_token']
   ```

3. **Validate API Key:**
   ```bash
   curl -H "Authorization: ApiKey your-api-key" \
        https://api.ecomate.com/v1/auth/validate
   ```

#### Issue: 403 Forbidden Error

**Symptoms:**
```json
{
  "error": "forbidden",
  "message": "Insufficient permissions for this operation"
}
```

**Solutions:**
1. Verify user role and permissions
2. Check system access permissions
3. Contact administrator for permission updates

### Rate Limiting Issues

#### Issue: 429 Too Many Requests

**Symptoms:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "API rate limit exceeded",
  "retry_after": 60
}
```

**Solutions:**

1. **Implement Exponential Backoff:**
   ```python
   import time
   import requests
   from requests.adapters import HTTPAdapter
   from urllib3.util.retry import Retry
   
   def create_session_with_retries():
       session = requests.Session()
       retry_strategy = Retry(
           total=3,
           backoff_factor=1,
           status_forcelist=[429, 500, 502, 503, 504],
       )
       adapter = HTTPAdapter(max_retries=retry_strategy)
       session.mount("http://", adapter)
       session.mount("https://", adapter)
       return session
   ```

2. **Check Rate Limit Headers:**
   ```python
   response = requests.get(url, headers=headers)
   
   print(f"Rate limit: {response.headers.get('X-RateLimit-Limit')}")
   print(f"Remaining: {response.headers.get('X-RateLimit-Remaining')}")
   print(f"Reset time: {response.headers.get('X-RateLimit-Reset')}")
   ```

3. **Implement Request Queuing:**
   ```python
   import queue
   import threading
   import time
   
   class RateLimitedClient:
       def __init__(self, requests_per_minute=60):
           self.requests_per_minute = requests_per_minute
           self.request_queue = queue.Queue()
           self.last_request_time = 0
           
       def make_request(self, method, url, **kwargs):
           current_time = time.time()
           time_since_last = current_time - self.last_request_time
           min_interval = 60.0 / self.requests_per_minute
           
           if time_since_last < min_interval:
               time.sleep(min_interval - time_since_last)
           
           response = requests.request(method, url, **kwargs)
           self.last_request_time = time.time()
           return response
   ```

### Data Validation Errors

#### Issue: 400 Bad Request - Invalid Parameters

**Symptoms:**
```json
{
  "error": "bad_request",
  "message": "Invalid parameter value",
  "details": {
    "field": "start_date",
    "issue": "Date format must be ISO 8601"
  }
}
```

**Solutions:**

1. **Date Format Validation:**
   ```python
   from datetime import datetime
   import pytz
   
   # Correct ISO 8601 format
   start_date = datetime.now(pytz.UTC).isoformat()
   # Output: 2024-01-15T10:30:00+00:00
   
   # Alternative format
   start_date = "2024-01-15T10:30:00Z"
   ```

2. **Parameter Validation:**
   ```python
   def validate_telemetry_request(system_id, start_date, end_date):
       errors = []
       
       # Validate system_id format
       if not system_id.startswith('sys_'):
           errors.append("system_id must start with 'sys_'")
       
       # Validate date range
       try:
           start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
           end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
           
           if start >= end:
               errors.append("start_date must be before end_date")
               
           # Check maximum range (30 days)
           if (end - start).days > 30:
               errors.append("Date range cannot exceed 30 days")
               
       except ValueError as e:
           errors.append(f"Invalid date format: {e}")
       
       return errors
   ```

### Connection and Timeout Issues

#### Issue: Connection Timeouts

**Symptoms:**
- Requests hanging indefinitely
- Connection timeout errors
- Intermittent failures

**Solutions:**

1. **Set Appropriate Timeouts:**
   ```python
   import requests
   
   # Set connection and read timeouts
   response = requests.get(
       url,
       headers=headers,
       timeout=(5, 30)  # (connection_timeout, read_timeout)
   )
   ```

2. **Implement Retry Logic:**
   ```python
   import requests
   from requests.exceptions import RequestException
   import time
   
   def make_request_with_retry(url, headers, max_retries=3):
       for attempt in range(max_retries):
           try:
               response = requests.get(url, headers=headers, timeout=(5, 30))
               response.raise_for_status()
               return response
           except RequestException as e:
               if attempt == max_retries - 1:
                   raise e
               time.sleep(2 ** attempt)  # Exponential backoff
   ```

### Data Inconsistency Issues

#### Issue: Missing or Null Data Points

**Symptoms:**
- Telemetry data with null values
- Missing timestamps in data series
- Inconsistent metric availability

**Solutions:**

1. **Handle Missing Data:**
   ```python
   def process_telemetry_data(data):
       processed_data = []
       
       for point in data:
           # Skip points with critical missing data
           if not point.get('timestamp'):
               continue
               
           # Fill missing metrics with defaults or interpolation
           metrics = point.get('metrics', {})
           
           # Use previous value for missing pH
           if 'ph' not in metrics and processed_data:
               metrics['ph'] = processed_data[-1]['metrics'].get('ph')
           
           processed_data.append({
               'timestamp': point['timestamp'],
               'metrics': metrics
           })
       
       return processed_data
   ```

2. **Validate Data Quality:**
   ```python
   def validate_data_quality(telemetry_point):
       quality_flags = telemetry_point.get('quality_flags', {})
       
       if quality_flags.get('data_quality') == 'poor':
           print(f"Warning: Poor data quality at {telemetry_point['timestamp']}")
           
       if quality_flags.get('calibration_due'):
           print(f"Warning: Sensor calibration due for system {telemetry_point['system_id']}")
   ```

## Debugging Tools

### API Response Inspection

```python
import requests
import json

def debug_api_call(method, url, **kwargs):
    print(f"Making {method} request to: {url}")
    print(f"Headers: {json.dumps(kwargs.get('headers', {}), indent=2)}")
    
    if 'json' in kwargs:
        print(f"Request body: {json.dumps(kwargs['json'], indent=2)}")
    
    response = requests.request(method, url, **kwargs)
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    try:
        response_json = response.json()
        print(f"Response body: {json.dumps(response_json, indent=2)}")
    except ValueError:
        print(f"Response body (text): {response.text}")
    
    return response
```

### Request Logging

```python
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)

# Create session with logging
session = requests.Session()
session.hooks['response'] = lambda r, *args, **kwargs: print(f"Response: {r.status_code} {r.url}")
```

### Health Check Endpoint

Use the health check endpoint to verify API connectivity:

```bash
curl -H "Authorization: ApiKey your-api-key" \
     https://api.ecomate.com/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "message_queue": "healthy"
  }
}
```

## Performance Optimization

### Efficient Data Retrieval

1. **Use Appropriate Time Intervals:**
   ```python
   # For real-time monitoring (last hour)
   params = {
       'start_date': (datetime.now() - timedelta(hours=1)).isoformat(),
       'end_date': datetime.now().isoformat(),
       'interval': '1m'
   }
   
   # For historical analysis (last month)
   params = {
       'start_date': (datetime.now() - timedelta(days=30)).isoformat(),
       'end_date': datetime.now().isoformat(),
       'interval': '1h'
   }
   ```

2. **Request Only Needed Metrics:**
   ```python
   # Instead of requesting all metrics
   params = {'metrics': 'ph,turbidity,flow_rate'}
   
   # Use specific metric filters
   response = requests.get(
       f"{base_url}/systems/{system_id}/telemetry",
       headers=headers,
       params=params
   )
   ```

3. **Implement Caching:**
   ```python
   import redis
   import json
   from datetime import timedelta
   
   redis_client = redis.Redis(host='localhost', port=6379, db=0)
   
   def get_cached_data(cache_key, fetch_function, ttl_seconds=300):
       # Try to get from cache first
       cached_data = redis_client.get(cache_key)
       
       if cached_data:
           return json.loads(cached_data)
       
       # Fetch fresh data
       fresh_data = fetch_function()
       
       # Cache the result
       redis_client.setex(
           cache_key,
           ttl_seconds,
           json.dumps(fresh_data)
       )
       
       return fresh_data
   ```

## Error Handling Best Practices

### Comprehensive Error Handling

```python
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
import logging

class EcoMateAPIClient:
    def __init__(self, api_key, base_url="https://api.ecomate.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'ApiKey {api_key}',
            'Content-Type': 'application/json'
        })
    
    def make_request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, timeout=(5, 30), **kwargs)
            
            # Handle different status codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise AuthenticationError("Invalid or expired credentials")
            elif response.status_code == 403:
                raise PermissionError("Insufficient permissions")
            elif response.status_code == 404:
                raise ResourceNotFoundError("Resource not found")
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
            elif response.status_code >= 500:
                raise ServerError(f"Server error: {response.status_code}")
            else:
                response.raise_for_status()
                
        except Timeout:
            logging.error(f"Request timeout for {url}")
            raise TimeoutError("Request timed out")
        except ConnectionError:
            logging.error(f"Connection error for {url}")
            raise ConnectionError("Unable to connect to API")
        except RequestException as e:
            logging.error(f"Request failed: {e}")
            raise APIError(f"API request failed: {e}")

# Custom exception classes
class APIError(Exception):
    pass

class AuthenticationError(APIError):
    pass

class RateLimitError(APIError):
    pass

class ResourceNotFoundError(APIError):
    pass

class ServerError(APIError):
    pass
```

## Getting Help

### Support Channels

1. **Documentation**: https://docs.ecomate.com/api
2. **Developer Forum**: https://community.ecomate.com/developers
3. **Email Support**: api-support@ecomate.com
4. **Status Page**: https://status.ecomate.com

### When Contacting Support

Include the following information:

1. **Request ID** (from response headers)
2. **Timestamp** of the issue
3. **HTTP method and endpoint** used
4. **Request headers** (excluding sensitive data)
5. **Request body** (if applicable)
6. **Full error response**
7. **Steps to reproduce** the issue

### Sample Support Request

```
Subject: API Error - 500 Internal Server Error on Telemetry Endpoint

Hello,

I'm experiencing a 500 Internal Server Error when calling the telemetry endpoint.

Details:
- Request ID: req_abc123456
- Timestamp: 2024-01-15T10:30:00Z
- Endpoint: GET /v1/systems/sys_12345/telemetry
- Parameters: start_date=2024-01-15T00:00:00Z&end_date=2024-01-15T10:00:00Z
- Error Response: {"error": "internal_error", "message": "An unexpected error occurred"}

This started happening around 10:00 AM EST today. The same request worked fine yesterday.

Please investigate and let me know if you need any additional information.

Thanks,
[Your Name]
```