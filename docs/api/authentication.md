# Authentication

## Overview

The EcoMate API uses multiple authentication methods to ensure secure access to wastewater treatment system data and controls. We support OAuth 2.0, API Key authentication, and JWT tokens for different use cases and security requirements.

## Authentication Methods

### 1. OAuth 2.0 (Recommended)

OAuth 2.0 is the preferred authentication method for production applications, providing secure, token-based access with fine-grained permissions.

#### Supported Grant Types

- **Authorization Code**: For web applications with server-side components
- **Client Credentials**: For server-to-server communication
- **Device Code**: For IoT devices and embedded systems
- **Refresh Token**: For long-lived access without re-authentication

#### Authorization Code Flow

**Step 1: Authorization Request**
```http
GET https://auth.ecomate.co.za/oauth/authorize?
  response_type=code&
  client_id=your_client_id&
  redirect_uri=https://yourapp.com/callback&
  scope=systems:read telemetry:read controls:write&
  state=random_state_string
```

**Step 2: Authorization Grant**
User is redirected to:
```http
https://yourapp.com/callback?
  code=authorization_code&
  state=random_state_string
```

**Step 3: Access Token Request**
```http
POST https://auth.ecomate.co.za/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=authorization_code&
redirect_uri=https://yourapp.com/callback&
client_id=your_client_id&
client_secret=your_client_secret
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def50200...",
  "scope": "systems:read telemetry:read controls:write"
}
```

#### Client Credentials Flow

For server-to-server authentication:

```http
POST https://auth.ecomate.co.za/oauth/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic base64(client_id:client_secret)

grant_type=client_credentials&
scope=systems:read telemetry:read
```

### 2. API Key Authentication

Simple authentication method suitable for development, testing, and basic integrations.

#### API Key Generation

1. **Login to Developer Portal**
   ```bash
   curl -X POST https://api.ecomate.co.za/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@company.com",
       "password": "your_password"
     }'
   ```

2. **Generate API Key**
   ```bash
   curl -X POST https://api.ecomate.co.za/v1/auth/api-keys \
     -H "Authorization: Bearer login_token" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Production Integration",
       "scopes": ["systems:read", "telemetry:read"],
       "expires_at": "2025-12-31T23:59:59Z"
     }'
   ```

#### Using API Keys

**Header Authentication (Recommended):**
```http
GET https://api.ecomate.co.za/v1/systems
Authorization: ApiKey your_api_key
```

**Query Parameter (Not Recommended):**
```http
GET https://api.ecomate.co.za/v1/systems?api_key=your_api_key
```

### 3. JWT Token Authentication

JSON Web Tokens for stateless authentication with embedded claims.

#### Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key_id"
  },
  "payload": {
    "iss": "https://auth.ecomate.co.za",
    "sub": "user_id",
    "aud": "https://api.ecomate.co.za",
    "exp": 1640995200,
    "iat": 1640991600,
    "scope": "systems:read telemetry:read",
    "client_id": "your_client_id",
    "system_ids": ["ECO-001-ZA", "ECO-002-ZA"]
  }
}
```

## Scopes and Permissions

### Available Scopes

| Scope | Description | Access Level |
|-------|-------------|-------------|
| `systems:read` | View system information | Read-only |
| `systems:write` | Modify system configuration | Read/Write |
| `telemetry:read` | Access sensor data | Read-only |
| `telemetry:write` | Submit telemetry data | Write-only |
| `controls:read` | View control states | Read-only |
| `controls:write` | Execute control commands | Write-only |
| `alerts:read` | Access alert information | Read-only |
| `alerts:write` | Manage alert configurations | Read/Write |
| `reports:read` | Generate and download reports | Read-only |
| `users:read` | View user information | Read-only |
| `users:write` | Manage user accounts | Read/Write |
| `admin` | Full administrative access | Full Access |

### Scope Combinations

**Monitoring Application:**
```
systems:read telemetry:read alerts:read reports:read
```

**Control System:**
```
systems:read controls:read controls:write telemetry:read
```

**Data Analytics:**
```
systems:read telemetry:read reports:read
```

**System Administrator:**
```
admin
```

## Security Best Practices

### Token Management

1. **Secure Storage**
   - Store tokens in secure, encrypted storage
   - Never log tokens in plain text
   - Use environment variables for configuration

2. **Token Rotation**
   ```python
   # Python example
   import os
   from datetime import datetime, timedelta
   
   def refresh_token_if_needed(token_info):
       if datetime.now() > token_info['expires_at'] - timedelta(minutes=5):
           return refresh_access_token(token_info['refresh_token'])
       return token_info
   ```

3. **Scope Minimization**
   - Request only necessary scopes
   - Use separate tokens for different functions
   - Regularly audit token permissions

### Network Security

1. **HTTPS Only**
   - All API calls must use HTTPS
   - Certificate pinning recommended
   - Validate SSL certificates

2. **IP Whitelisting**
   ```json
   {
     "api_key_id": "key_123",
     "allowed_ips": [
       "203.0.113.0/24",
       "198.51.100.50"
     ]
   }
   ```

3. **Rate Limiting**
   - Implement client-side rate limiting
   - Handle 429 responses gracefully
   - Use exponential backoff for retries

### Error Handling

#### Authentication Errors

```json
{
  "error": "invalid_token",
  "error_description": "The access token provided is expired, revoked, malformed, or invalid",
  "error_code": "AUTH_001",
  "timestamp": "2025-01-24T10:30:00Z"
}
```

#### Common Error Codes

| Code | HTTP Status | Description | Action |
|------|-------------|-------------|--------|
| AUTH_001 | 401 | Invalid or expired token | Refresh token |
| AUTH_002 | 401 | Invalid API key | Check API key |
| AUTH_003 | 403 | Insufficient permissions | Request additional scopes |
| AUTH_004 | 429 | Rate limit exceeded | Implement backoff |
| AUTH_005 | 400 | Invalid grant type | Check OAuth flow |

## Code Examples

### Python

```python
import requests
from requests.auth import HTTPBasicAuth

class EcoMateAuth:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.refresh_token = None
    
    def get_access_token(self):
        """Get access token using client credentials flow"""
        url = "https://auth.ecomate.co.za/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "scope": "systems:read telemetry:read"
        }
        
        response = requests.post(
            url,
            data=data,
            auth=HTTPBasicAuth(self.client_id, self.client_secret)
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            return self.access_token
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    def make_authenticated_request(self, url):
        """Make API request with authentication"""
        if not self.access_token:
            self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 401:
            # Token expired, refresh and retry
            self.get_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = requests.get(url, headers=headers)
        
        return response

# Usage
auth = EcoMateAuth("your_client_id", "your_client_secret")
response = auth.make_authenticated_request("https://api.ecomate.co.za/v1/systems")
print(response.json())
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

class EcoMateAuth {
    constructor(clientId, clientSecret) {
        this.clientId = clientId;
        this.clientSecret = clientSecret;
        this.accessToken = null;
        this.tokenExpiry = null;
    }

    async getAccessToken() {
        const url = 'https://auth.ecomate.co.za/oauth/token';
        const data = {
            grant_type: 'client_credentials',
            scope: 'systems:read telemetry:read'
        };

        const config = {
            auth: {
                username: this.clientId,
                password: this.clientSecret
            }
        };

        try {
            const response = await axios.post(url, data, config);
            this.accessToken = response.data.access_token;
            this.tokenExpiry = Date.now() + (response.data.expires_in * 1000);
            return this.accessToken;
        } catch (error) {
            throw new Error(`Authentication failed: ${error.response.data}`);
        }
    }

    async makeAuthenticatedRequest(url) {
        if (!this.accessToken || Date.now() >= this.tokenExpiry) {
            await this.getAccessToken();
        }

        const config = {
            headers: {
                'Authorization': `Bearer ${this.accessToken}`,
                'Content-Type': 'application/json'
            }
        };

        try {
            const response = await axios.get(url, config);
            return response.data;
        } catch (error) {
            if (error.response.status === 401) {
                // Token expired, refresh and retry
                await this.getAccessToken();
                config.headers.Authorization = `Bearer ${this.accessToken}`;
                const retryResponse = await axios.get(url, config);
                return retryResponse.data;
            }
            throw error;
        }
    }
}

// Usage
const auth = new EcoMateAuth('your_client_id', 'your_client_secret');
auth.makeAuthenticatedRequest('https://api.ecomate.co.za/v1/systems')
    .then(data => console.log(data))
    .catch(error => console.error(error));
```

## Testing Authentication

### Postman Collection

```json
{
  "info": {
    "name": "EcoMate API Authentication",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "oauth2",
    "oauth2": [
      {
        "key": "tokenUrl",
        "value": "https://auth.ecomate.co.za/oauth/token",
        "type": "string"
      },
      {
        "key": "grant_type",
        "value": "client_credentials",
        "type": "string"
      }
    ]
  }
}
```

### cURL Examples

**Test API Key Authentication:**
```bash
curl -X GET "https://api.ecomate.co.za/v1/systems" \
  -H "Authorization: ApiKey your_api_key" \
  -H "Accept: application/json"
```

**Test OAuth Token:**
```bash
curl -X GET "https://api.ecomate.co.za/v1/systems" \
  -H "Authorization: Bearer your_access_token" \
  -H "Accept: application/json"
```

## Troubleshooting

### Common Issues

1. **Token Expired**
   - **Symptom**: 401 Unauthorized responses
   - **Solution**: Implement automatic token refresh

2. **Invalid Scope**
   - **Symptom**: 403 Forbidden responses
   - **Solution**: Request appropriate scopes during authentication

3. **Rate Limiting**
   - **Symptom**: 429 Too Many Requests
   - **Solution**: Implement exponential backoff and respect rate limits

4. **SSL Certificate Issues**
   - **Symptom**: SSL verification errors
   - **Solution**: Ensure proper certificate validation

### Debug Mode

Enable debug logging to troubleshoot authentication issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your authentication code here
```

---

**Last Updated**: January 2025 | **Version**: 2.1  
**Contact**: For authentication issues, contact [auth-support@ecomate.co.za](mailto:auth-support@ecomate.co.za)