# Software Development Kits (SDKs)

EcoMate provides official SDKs for popular programming languages to simplify API integration and reduce development time.

## Available SDKs

### Python SDK

**Installation:**
```bash
pip install ecomate-python-sdk
```

**Quick Start:**
```python
from ecomate import EcoMateClient

# Initialize client
client = EcoMateClient(api_key="your-api-key")

# Get system status
system = client.systems.get("sys_12345")
print(f"System status: {system.status}")

# Retrieve telemetry data
telemetry = client.telemetry.get(
    system_id="sys_12345",
    start_date="2024-01-01T00:00:00Z",
    end_date="2024-01-02T00:00:00Z",
    metrics=["ph", "turbidity", "flow_rate"]
)

for point in telemetry.data:
    print(f"{point.timestamp}: pH={point.metrics.ph}")
```

**Advanced Features:**
```python
# Async support
import asyncio
from ecomate import AsyncEcoMateClient

async def main():
    async with AsyncEcoMateClient(api_key="your-api-key") as client:
        # Concurrent requests
        systems_task = client.systems.list()
        alerts_task = client.alerts.get_active()
        
        systems, alerts = await asyncio.gather(systems_task, alerts_task)
        
        print(f"Found {len(systems)} systems and {len(alerts)} active alerts")

asyncio.run(main())
```

**Error Handling:**
```python
from ecomate import EcoMateClient, EcoMateError, AuthenticationError, RateLimitError

client = EcoMateClient(api_key="your-api-key")

try:
    system = client.systems.get("sys_12345")
except AuthenticationError:
    print("Invalid API key or expired token")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except EcoMateError as e:
    print(f"API error: {e.message}")
```

### JavaScript/Node.js SDK

**Installation:**
```bash
npm install @ecomate/sdk
# or
yarn add @ecomate/sdk
```

**Quick Start:**
```javascript
const { EcoMateClient } = require('@ecomate/sdk');

// Initialize client
const client = new EcoMateClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.ecomate.com/v1'
});

// Get system status
async function getSystemStatus() {
  try {
    const system = await client.systems.get('sys_12345');
    console.log(`System status: ${system.status}`);
    
    // Get telemetry data
    const telemetry = await client.telemetry.get({
      systemId: 'sys_12345',
      startDate: '2024-01-01T00:00:00Z',
      endDate: '2024-01-02T00:00:00Z',
      metrics: ['ph', 'turbidity', 'flow_rate']
    });
    
    telemetry.data.forEach(point => {
      console.log(`${point.timestamp}: pH=${point.metrics.ph}`);
    });
    
  } catch (error) {
    console.error('API Error:', error.message);
  }
}

getSystemStatus();
```

**TypeScript Support:**
```typescript
import { EcoMateClient, System, TelemetryData } from '@ecomate/sdk';

interface SystemMetrics {
  ph: number;
  turbidity: number;
  flowRate: number;
}

const client = new EcoMateClient({
  apiKey: process.env.ECOMATE_API_KEY!,
});

async function analyzeSystemPerformance(systemId: string): Promise<void> {
  const system: System = await client.systems.get(systemId);
  
  const telemetry: TelemetryData = await client.telemetry.get({
    systemId,
    startDate: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    endDate: new Date().toISOString(),
    interval: '1h'
  });
  
  const avgMetrics = calculateAverages(telemetry.data);
  console.log('24-hour averages:', avgMetrics);
}

function calculateAverages(data: any[]): SystemMetrics {
  const totals = data.reduce((acc, point) => ({
    ph: acc.ph + point.metrics.ph,
    turbidity: acc.turbidity + point.metrics.turbidity,
    flowRate: acc.flowRate + point.metrics.flow_rate
  }), { ph: 0, turbidity: 0, flowRate: 0 });
  
  const count = data.length;
  return {
    ph: totals.ph / count,
    turbidity: totals.turbidity / count,
    flowRate: totals.flowRate / count
  };
}
```

### Java SDK

**Installation (Maven):**
```xml
<dependency>
    <groupId>com.ecomate</groupId>
    <artifactId>ecomate-java-sdk</artifactId>
    <version>1.0.0</version>
</dependency>
```

**Installation (Gradle):**
```gradle
implementation 'com.ecomate:ecomate-java-sdk:1.0.0'
```

**Quick Start:**
```java
import com.ecomate.sdk.EcoMateClient;
import com.ecomate.sdk.models.System;
import com.ecomate.sdk.models.TelemetryData;
import com.ecomate.sdk.exceptions.EcoMateException;

public class EcoMateExample {
    public static void main(String[] args) {
        // Initialize client
        EcoMateClient client = EcoMateClient.builder()
            .apiKey("your-api-key")
            .baseUrl("https://api.ecomate.com/v1")
            .build();
        
        try {
            // Get system status
            System system = client.systems().get("sys_12345");
            System.out.println("System status: " + system.getStatus());
            
            // Get telemetry data
            TelemetryData telemetry = client.telemetry()
                .systemId("sys_12345")
                .startDate("2024-01-01T00:00:00Z")
                .endDate("2024-01-02T00:00:00Z")
                .metrics(Arrays.asList("ph", "turbidity", "flow_rate"))
                .get();
            
            telemetry.getData().forEach(point -> {
                System.out.println(point.getTimestamp() + ": pH=" + 
                    point.getMetrics().getPh());
            });
            
        } catch (EcoMateException e) {
            System.err.println("API Error: " + e.getMessage());
        }
    }
}
```

**Spring Boot Integration:**
```java
@Configuration
public class EcoMateConfig {
    
    @Value("${ecomate.api.key}")
    private String apiKey;
    
    @Bean
    public EcoMateClient ecoMateClient() {
        return EcoMateClient.builder()
            .apiKey(apiKey)
            .connectionTimeout(Duration.ofSeconds(10))
            .readTimeout(Duration.ofSeconds(30))
            .retryPolicy(RetryPolicy.exponentialBackoff(3))
            .build();
    }
}

@Service
public class SystemMonitoringService {
    
    @Autowired
    private EcoMateClient ecoMateClient;
    
    @Scheduled(fixedRate = 60000) // Every minute
    public void checkSystemAlerts() {
        try {
            List<Alert> alerts = ecoMateClient.alerts()
                .status(AlertStatus.ACTIVE)
                .severity(AlertSeverity.HIGH, AlertSeverity.CRITICAL)
                .list();
            
            alerts.forEach(this::processAlert);
            
        } catch (EcoMateException e) {
            log.error("Failed to fetch alerts", e);
        }
    }
    
    private void processAlert(Alert alert) {
        // Process high-priority alerts
        log.warn("High priority alert: {} for system {}", 
            alert.getMessage(), alert.getSystemId());
    }
}
```

### C# SDK

**Installation (NuGet):**
```bash
Install-Package EcoMate.SDK
# or
dotnet add package EcoMate.SDK
```

**Quick Start:**
```csharp
using EcoMate.SDK;
using EcoMate.SDK.Models;

class Program
{
    static async Task Main(string[] args)
    {
        // Initialize client
        var client = new EcoMateClient("your-api-key");
        
        try
        {
            // Get system status
            var system = await client.Systems.GetAsync("sys_12345");
            Console.WriteLine($"System status: {system.Status}");
            
            // Get telemetry data
            var telemetryRequest = new TelemetryRequest
            {
                SystemId = "sys_12345",
                StartDate = DateTime.UtcNow.AddDays(-1),
                EndDate = DateTime.UtcNow,
                Metrics = new[] { "ph", "turbidity", "flow_rate" },
                Interval = "1h"
            };
            
            var telemetry = await client.Telemetry.GetAsync(telemetryRequest);
            
            foreach (var point in telemetry.Data)
            {
                Console.WriteLine($"{point.Timestamp}: pH={point.Metrics.Ph}");
            }
        }
        catch (EcoMateException ex)
        {
            Console.WriteLine($"API Error: {ex.Message}");
        }
    }
}
```

**Dependency Injection (.NET Core):**
```csharp
// Startup.cs or Program.cs
services.AddEcoMateClient(options =>
{
    options.ApiKey = Configuration["EcoMate:ApiKey"];
    options.BaseUrl = "https://api.ecomate.com/v1";
    options.Timeout = TimeSpan.FromSeconds(30);
});

// Service class
public class SystemService
{
    private readonly IEcoMateClient _ecoMateClient;
    
    public SystemService(IEcoMateClient ecoMateClient)
    {
        _ecoMateClient = ecoMateClient;
    }
    
    public async Task<List<SystemAlert>> GetCriticalAlertsAsync()
    {
        var alerts = await _ecoMateClient.Alerts.GetActiveAsync(
            severity: AlertSeverity.Critical);
        
        return alerts.Where(a => a.CreatedAt > DateTime.UtcNow.AddHours(-1))
                    .ToList();
    }
}
```

### Go SDK

**Installation:**
```bash
go get github.com/ecomate/ecomate-go-sdk
```

**Quick Start:**
```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"
    
    "github.com/ecomate/ecomate-go-sdk"
)

func main() {
    // Initialize client
    client := ecomate.NewClient("your-api-key")
    
    ctx := context.Background()
    
    // Get system status
    system, err := client.Systems.Get(ctx, "sys_12345")
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("System status: %s\n", system.Status)
    
    // Get telemetry data
    telemetryReq := &ecomate.TelemetryRequest{
        SystemID:  "sys_12345",
        StartDate: time.Now().Add(-24 * time.Hour),
        EndDate:   time.Now(),
        Metrics:   []string{"ph", "turbidity", "flow_rate"},
        Interval:  "1h",
    }
    
    telemetry, err := client.Telemetry.Get(ctx, telemetryReq)
    if err != nil {
        log.Fatal(err)
    }
    
    for _, point := range telemetry.Data {
        fmt.Printf("%s: pH=%.2f\n", point.Timestamp, point.Metrics.Ph)
    }
}
```

**With Context and Cancellation:**
```go
func monitorSystemWithTimeout(client *ecomate.Client, systemID string) {
    // Create context with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    // Monitor alerts with cancellation support
    alertsChan := make(chan *ecomate.Alert)
    errorsChan := make(chan error)
    
    go func() {
        for {
            select {
            case <-ctx.Done():
                return
            default:
                alerts, err := client.Alerts.GetActive(ctx, systemID)
                if err != nil {
                    errorsChan <- err
                    return
                }
                
                for _, alert := range alerts {
                    alertsChan <- alert
                }
                
                time.Sleep(10 * time.Second)
            }
        }
    }()
    
    // Process alerts
    for {
        select {
        case alert := <-alertsChan:
            fmt.Printf("Alert: %s (Severity: %s)\n", alert.Message, alert.Severity)
        case err := <-errorsChan:
            log.Printf("Error monitoring alerts: %v", err)
        case <-ctx.Done():
            fmt.Println("Monitoring stopped")
            return
        }
    }
}
```

## SDK Features Comparison

| Feature | Python | JavaScript | Java | C# | Go |
|---------|--------|------------|------|----|----||
| Async/Await Support | ✅ | ✅ | ✅ | ✅ | ✅ |
| Type Safety | ✅* | ✅** | ✅ | ✅ | ✅ |
| Retry Logic | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rate Limiting | ✅ | ✅ | ✅ | ✅ | ✅ |
| Caching | ✅ | ✅ | ✅ | ✅ | ✅ |
| Streaming | ✅ | ✅ | ✅ | ✅ | ✅ |
| Webhooks | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mock Testing | ✅ | ✅ | ✅ | ✅ | ✅ |

*With type hints  
**With TypeScript

## Common SDK Patterns

### Configuration Management

**Environment Variables:**
```bash
# .env file
ECOMATE_API_KEY=your-api-key
ECOMATE_BASE_URL=https://api.ecomate.com/v1
ECOMATE_TIMEOUT=30
ECOMATE_RETRY_ATTEMPTS=3
```

**Configuration Files:**
```yaml
# config.yaml
ecomate:
  api_key: ${ECOMATE_API_KEY}
  base_url: https://api.ecomate.com/v1
  timeout: 30
  retry:
    attempts: 3
    backoff_factor: 2
  rate_limit:
    requests_per_minute: 60
```

### Error Handling Patterns

**Retry with Exponential Backoff:**
```python
import time
import random
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                except (ConnectionError, TimeoutError) as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def get_system_data(system_id):
    return client.systems.get(system_id)
```

### Caching Strategies

**In-Memory Caching:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedEcoMateClient:
    def __init__(self, client):
        self.client = client
        self._cache = {}
    
    def get_system_with_cache(self, system_id, ttl_minutes=5):
        cache_key = f"system_{system_id}"
        now = datetime.now()
        
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if now - timestamp < timedelta(minutes=ttl_minutes):
                return cached_data
        
        # Fetch fresh data
        system = self.client.systems.get(system_id)
        self._cache[cache_key] = (system, now)
        
        return system
```

### Batch Operations

**Bulk Data Retrieval:**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class BatchEcoMateClient:
    def __init__(self, client, max_workers=5):
        self.client = client
        self.max_workers = max_workers
    
    def get_multiple_systems(self, system_ids):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.client.systems.get, system_id): system_id 
                for system_id in system_ids
            }
            
            results = {}
            for future in futures:
                system_id = futures[future]
                try:
                    results[system_id] = future.result()
                except Exception as e:
                    results[system_id] = {'error': str(e)}
            
            return results
    
    async def get_multiple_systems_async(self, system_ids):
        async with AsyncEcoMateClient(api_key=self.client.api_key) as async_client:
            tasks = [
                async_client.systems.get(system_id) 
                for system_id in system_ids
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                system_id: result if not isinstance(result, Exception) else {'error': str(result)}
                for system_id, result in zip(system_ids, results)
            }
```

## Testing with SDKs

### Mock Testing

**Python (pytest):**
```python
import pytest
from unittest.mock import Mock, patch
from ecomate import EcoMateClient

@pytest.fixture
def mock_client():
    client = Mock(spec=EcoMateClient)
    return client

def test_system_status_check(mock_client):
    # Mock response
    mock_system = Mock()
    mock_system.status = "operational"
    mock_client.systems.get.return_value = mock_system
    
    # Test function
    result = check_system_health(mock_client, "sys_12345")
    
    # Assertions
    assert result == "healthy"
    mock_client.systems.get.assert_called_once_with("sys_12345")

def check_system_health(client, system_id):
    system = client.systems.get(system_id)
    return "healthy" if system.status == "operational" else "unhealthy"
```

**JavaScript (Jest):**
```javascript
const { EcoMateClient } = require('@ecomate/sdk');

jest.mock('@ecomate/sdk');

describe('System Monitoring', () => {
  let mockClient;
  
  beforeEach(() => {
    mockClient = new EcoMateClient();
  });
  
  test('should return system status', async () => {
    // Mock implementation
    mockClient.systems.get.mockResolvedValue({
      id: 'sys_12345',
      status: 'operational'
    });
    
    const result = await getSystemStatus(mockClient, 'sys_12345');
    
    expect(result.status).toBe('operational');
    expect(mockClient.systems.get).toHaveBeenCalledWith('sys_12345');
  });
});

async function getSystemStatus(client, systemId) {
  return await client.systems.get(systemId);
}
```

## Migration Guide

### Upgrading SDK Versions

**Breaking Changes in v2.0:**

1. **Method Renaming:**
   ```python
   # v1.x
   client.get_system("sys_12345")
   
   # v2.x
   client.systems.get("sys_12345")
   ```

2. **Response Structure Changes:**
   ```python
   # v1.x
   telemetry = client.get_telemetry(system_id, start_date, end_date)
   for point in telemetry:
       print(point['ph'])
   
   # v2.x
   telemetry = client.telemetry.get(system_id=system_id, start_date=start_date, end_date=end_date)
   for point in telemetry.data:
       print(point.metrics.ph)
   ```

3. **Error Handling:**
   ```python
   # v1.x
   try:
       system = client.get_system("sys_12345")
   except APIError as e:
       print(e.message)
   
   # v2.x
   try:
       system = client.systems.get("sys_12345")
   except EcoMateException as e:
       print(e.message)
   ```

## Support and Resources

### Documentation
- **API Reference**: https://docs.ecomate.com/api
- **SDK Documentation**: https://docs.ecomate.com/sdks
- **Code Examples**: https://github.com/ecomate/examples

### Community
- **GitHub Issues**: Report bugs and request features
- **Developer Forum**: https://community.ecomate.com/developers
- **Stack Overflow**: Tag questions with `ecomate-api`

### Support
- **Email**: sdk-support@ecomate.com
- **Response Time**: 24-48 hours for technical issues
- **Priority Support**: Available for enterprise customers