"""Redis fixtures and mock data for caching and session testing."""

import pytest
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Union
from unittest.mock import Mock, AsyncMock

from redis.asyncio import Redis


@pytest.fixture
async def mock_redis_client():
    """Create a mock Redis client for testing."""
    client = Mock(spec=Redis)
    
    # Mock storage for testing
    mock_storage = {}
    
    async def mock_get(key: str) -> Optional[bytes]:
        value = mock_storage.get(key)
        return value.encode() if value else None
    
    async def mock_set(key: str, value: Union[str, bytes], ex: Optional[int] = None) -> bool:
        if isinstance(value, bytes):
            value = value.decode()
        mock_storage[key] = value
        return True
    
    async def mock_delete(*keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in mock_storage:
                del mock_storage[key]
                deleted += 1
        return deleted
    
    async def mock_exists(*keys: str) -> int:
        return sum(1 for key in keys if key in mock_storage)
    
    async def mock_expire(key: str, seconds: int) -> bool:
        return key in mock_storage
    
    async def mock_ttl(key: str) -> int:
        return 3600 if key in mock_storage else -2
    
    async def mock_keys(pattern: str = "*") -> List[bytes]:
        if pattern == "*":
            return [key.encode() for key in mock_storage.keys()]
        # Simple pattern matching for testing
        import fnmatch
        return [key.encode() for key in mock_storage.keys() if fnmatch.fnmatch(key, pattern)]
    
    async def mock_flushdb() -> bool:
        mock_storage.clear()
        return True
    
    async def mock_hget(name: str, key: str) -> Optional[bytes]:
        hash_data = mock_storage.get(name, {})
        if isinstance(hash_data, str):
            hash_data = json.loads(hash_data)
        value = hash_data.get(key)
        return value.encode() if value else None
    
    async def mock_hset(name: str, key: str, value: Union[str, bytes]) -> int:
        if isinstance(value, bytes):
            value = value.decode()
        
        hash_data = mock_storage.get(name, {})
        if isinstance(hash_data, str):
            hash_data = json.loads(hash_data)
        
        hash_data[key] = value
        mock_storage[name] = json.dumps(hash_data)
        return 1
    
    async def mock_hgetall(name: str) -> Dict[bytes, bytes]:
        hash_data = mock_storage.get(name, {})
        if isinstance(hash_data, str):
            hash_data = json.loads(hash_data)
        return {k.encode(): v.encode() for k, v in hash_data.items()}
    
    async def mock_hdel(name: str, *keys: str) -> int:
        hash_data = mock_storage.get(name, {})
        if isinstance(hash_data, str):
            hash_data = json.loads(hash_data)
        
        deleted = 0
        for key in keys:
            if key in hash_data:
                del hash_data[key]
                deleted += 1
        
        mock_storage[name] = json.dumps(hash_data)
        return deleted
    
    async def mock_lpush(name: str, *values: Union[str, bytes]) -> int:
        list_data = mock_storage.get(name, [])
        if isinstance(list_data, str):
            list_data = json.loads(list_data)
        
        for value in reversed(values):
            if isinstance(value, bytes):
                value = value.decode()
            list_data.insert(0, value)
        
        mock_storage[name] = json.dumps(list_data)
        return len(list_data)
    
    async def mock_rpop(name: str) -> Optional[bytes]:
        list_data = mock_storage.get(name, [])
        if isinstance(list_data, str):
            list_data = json.loads(list_data)
        
        if list_data:
            value = list_data.pop()
            mock_storage[name] = json.dumps(list_data)
            return value.encode()
        return None
    
    async def mock_llen(name: str) -> int:
        list_data = mock_storage.get(name, [])
        if isinstance(list_data, str):
            list_data = json.loads(list_data)
        return len(list_data)
    
    # Configure mock methods
    client.get = mock_get
    client.set = mock_set
    client.delete = mock_delete
    client.exists = mock_exists
    client.expire = mock_expire
    client.ttl = mock_ttl
    client.keys = mock_keys
    client.flushdb = mock_flushdb
    client.hget = mock_hget
    client.hset = mock_hset
    client.hgetall = mock_hgetall
    client.hdel = mock_hdel
    client.lpush = mock_lpush
    client.rpop = mock_rpop
    client.llen = mock_llen
    client.close = AsyncMock()
    
    # Add storage access for testing
    client._mock_storage = mock_storage
    
    return client


@pytest.fixture
def sample_cache_data():
    """Create sample cache data for testing."""
    return {
        "product_cache_data": {
            "product:1": json.dumps({
                "id": 1,
                "name": "AquaTech Centrifugal Pump CP-100",
                "category": "pumps",
                "price": "1500.00",
                "currency": "USD",
                "specifications": {
                    "flow_rate": 100,
                    "head_pressure": 45,
                    "power_consumption": 750,
                    "material": "stainless steel"
                },
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl_seconds": 3600
            }),
            "product:2": json.dumps({
                "id": 2,
                "name": "WaterTech Pro UV Reactor UV-55R",
                "category": "uv_reactors",
                "price": "850.00",
                "currency": "USD",
                "specifications": {
                    "uv_dose": 40,
                    "flow_rate": 10,
                    "lamp_power": 55,
                    "reactor_material": "stainless steel 316L"
                },
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl_seconds": 3600
            }),
            "product:3": json.dumps({
                "id": 3,
                "name": "Industrial Heavy-Duty Pump HD-500",
                "category": "pumps",
                "price": "3200.00",
                "currency": "USD",
                "specifications": {
                    "flow_rate": 300,
                    "head_pressure": 120,
                    "power_consumption": 2200,
                    "material": "duplex stainless steel"
                },
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl_seconds": 3600
            })
        },
        "search_cache_data": {
            "search:pumps:flow_rate_100": json.dumps({
                "query": "pumps with flow rate 100",
                "results": [
                    {"id": 1, "name": "AquaTech Centrifugal Pump CP-100", "score": 0.95},
                    {"id": 4, "name": "FlowMax Pump FM-100", "score": 0.88}
                ],
                "total_results": 2,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl_seconds": 1800
            }),
            "search:uv_reactors:residential": json.dumps({
                "query": "residential UV reactors",
                "results": [
                    {"id": 2, "name": "WaterTech Pro UV Reactor UV-55R", "score": 0.92},
                    {"id": 5, "name": "HomeClean UV System HC-25", "score": 0.85}
                ],
                "total_results": 2,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl_seconds": 1800
            })
        },
        "price_history_cache_data": {
            "price_history:1": json.dumps([
                {
                    "price": "1500.00",
                    "currency": "USD",
                    "recorded_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
                    "source": "supplier_website"
                },
                {
                    "price": "1525.00",
                    "currency": "USD",
                    "recorded_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
                    "source": "supplier_website"
                },
                {
                    "price": "1575.00",
                    "currency": "USD",
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                    "source": "supplier_website"
                }
            ]),
            "price_history:2": json.dumps([
                {
                    "price": "850.00",
                    "currency": "USD",
                    "recorded_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
                    "source": "supplier_website"
                },
                {
                    "price": "825.00",
                    "currency": "USD",
                    "recorded_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                    "source": "supplier_website"
                }
            ])
        },
        "workflow_cache_data": {
            "workflow:research-workflow-123": json.dumps({
                "workflow_id": "research-workflow-123",
                "status": "running",
                "progress": 65,
                "current_step": "parsing_product_data",
                "started_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
                "estimated_completion": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
                "products_processed": 2,
                "products_total": 3
            }),
            "workflow:price-monitoring-456": json.dumps({
                "workflow_id": "price-monitoring-456",
                "status": "active",
                "last_check": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "next_check": (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat(),
                "products_monitored": 5,
                "price_changes_detected": 2,
                "alerts_sent": 2
            })
        }
    }


@pytest.fixture
def sample_session_data():
    """Create sample session data for testing."""
    return {
        "user_sessions": {
            "session:user-123:abc123def456": json.dumps({
                "user_id": "user-123",
                "session_id": "abc123def456",
                "created_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "last_activity": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "preferences": {
                    "theme": "dark",
                    "language": "en",
                    "notifications_enabled": True
                },
                "active_workflows": ["research-workflow-123"],
                "recent_searches": [
                    "centrifugal pumps",
                    "UV reactors residential",
                    "stainless steel pumps"
                ]
            }),
            "session:user-456:xyz789ghi012": json.dumps({
                "user_id": "user-456",
                "session_id": "xyz789ghi012",
                "created_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "ip_address": "10.0.0.50",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "preferences": {
                    "theme": "light",
                    "language": "en",
                    "notifications_enabled": False
                },
                "active_workflows": ["price-monitoring-456"],
                "recent_searches": [
                    "industrial pumps",
                    "high pressure pumps"
                ]
            })
        },
        "api_rate_limits": {
            "rate_limit:user-123:api_calls": "45",  # 45 calls in current window
            "rate_limit:user-456:api_calls": "12",  # 12 calls in current window
            "rate_limit:ip:192.168.1.100:scraping": "25",  # 25 scraping requests
            "rate_limit:ip:10.0.0.50:scraping": "8"   # 8 scraping requests
        },
        "temporary_data": {
            "temp:upload:user-123:file-abc": json.dumps({
                "filename": "product_list.csv",
                "size_bytes": 15420,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "processing_status": "pending",
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            }),
            "temp:export:user-456:report-xyz": json.dumps({
                "report_type": "price_monitoring_summary",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "file_path": "/tmp/reports/price_monitoring_summary_456.pdf",
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
            })
        }
    }


@pytest.fixture
def sample_queue_data():
    """Create sample queue data for testing."""
    return {
        "scraping_queue": [
            json.dumps({
                "task_id": "scrape-001",
                "url": "https://aquatech-solutions.com/centrifugal-pump-cp-100",
                "category": "pumps",
                "priority": "high",
                "retry_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "user_id": "user-123",
                "workflow_id": "research-workflow-123"
            }),
            json.dumps({
                "task_id": "scrape-002",
                "url": "https://watertech-pro.com/uv-reactor-uv-55r",
                "category": "uv_reactors",
                "priority": "medium",
                "retry_count": 1,
                "created_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
                "user_id": "user-123",
                "workflow_id": "research-workflow-123"
            })
        ],
        "notification_queue": [
            json.dumps({
                "notification_id": "notif-001",
                "type": "workflow_completed",
                "recipient": "user@example.com",
                "subject": "Research Workflow Completed",
                "message": "Your product research workflow has completed successfully.",
                "priority": "normal",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "attempts": 0
            }),
            json.dumps({
                "notification_id": "notif-002",
                "type": "price_alert",
                "recipient": "user2@example.com",
                "subject": "Price Change Alert",
                "message": "Price change detected for AquaTech Centrifugal Pump CP-100",
                "priority": "high",
                "created_at": (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat(),
                "attempts": 1
            })
        ],
        "processing_queue": [
            json.dumps({
                "task_id": "process-001",
                "type": "data_validation",
                "data": {
                    "product_id": 1,
                    "validation_rules": ["price_format", "specification_completeness"]
                },
                "priority": "medium",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "estimated_duration_seconds": 30
            })
        ]
    }


@pytest.fixture
def cache_performance_scenarios():
    """Create cache performance testing scenarios."""
    return {
        "hit_rate_scenarios": [
            {
                "scenario_name": "high_hit_rate",
                "cache_size": 1000,
                "request_pattern": "80_20_rule",  # 80% requests for 20% of data
                "expected_hit_rate": 0.85
            },
            {
                "scenario_name": "medium_hit_rate",
                "cache_size": 500,
                "request_pattern": "uniform",
                "expected_hit_rate": 0.60
            },
            {
                "scenario_name": "low_hit_rate",
                "cache_size": 100,
                "request_pattern": "random",
                "expected_hit_rate": 0.30
            }
        ],
        "eviction_scenarios": [
            {
                "eviction_policy": "LRU",
                "cache_size": 100,
                "data_size": 150,
                "expected_evictions": 50
            },
            {
                "eviction_policy": "TTL",
                "cache_size": 200,
                "ttl_seconds": 300,
                "expected_expired_items": 25
            }
        ],
        "concurrency_scenarios": [
            {
                "concurrent_readers": 10,
                "concurrent_writers": 2,
                "operation_duration_seconds": 60,
                "expected_conflicts": 0
            },
            {
                "concurrent_readers": 50,
                "concurrent_writers": 10,
                "operation_duration_seconds": 120,
                "expected_conflicts": 5
            }
        ]
    }


@pytest.fixture
def redis_error_scenarios():
    """Create Redis error scenarios for testing."""
    return {
        "connection_errors": [
            {
                "error_type": "ConnectionError",
                "error_message": "Connection refused",
                "retry_strategy": "exponential_backoff",
                "max_retries": 3
            },
            {
                "error_type": "TimeoutError",
                "error_message": "Operation timed out",
                "retry_strategy": "immediate",
                "max_retries": 2
            }
        ],
        "memory_errors": [
            {
                "error_type": "OutOfMemoryError",
                "error_message": "Redis server out of memory",
                "fallback_strategy": "use_database",
                "alert_required": True
            }
        ],
        "data_errors": [
            {
                "error_type": "SerializationError",
                "error_message": "Failed to serialize data",
                "fallback_strategy": "skip_cache",
                "log_level": "warning"
            },
            {
                "error_type": "DeserializationError",
                "error_message": "Failed to deserialize cached data",
                "fallback_strategy": "refresh_cache",
                "log_level": "error"
            }
        ]
    }


@pytest.fixture
def cache_key_patterns():
    """Create cache key patterns for testing."""
    return {
        "product_keys": {
            "pattern": "product:{product_id}",
            "examples": ["product:1", "product:2", "product:123"]
        },
        "search_keys": {
            "pattern": "search:{category}:{query_hash}",
            "examples": [
                "search:pumps:abc123",
                "search:uv_reactors:def456",
                "search:all:xyz789"
            ]
        },
        "user_keys": {
            "pattern": "user:{user_id}:{data_type}",
            "examples": [
                "user:123:preferences",
                "user:456:recent_searches",
                "user:789:active_workflows"
            ]
        },
        "workflow_keys": {
            "pattern": "workflow:{workflow_id}:{data_type}",
            "examples": [
                "workflow:research-123:status",
                "workflow:monitoring-456:progress",
                "workflow:processing-789:results"
            ]
        },
        "rate_limit_keys": {
            "pattern": "rate_limit:{identifier}:{action}",
            "examples": [
                "rate_limit:user-123:api_calls",
                "rate_limit:ip-192.168.1.1:scraping",
                "rate_limit:workflow-456:notifications"
            ]
        },
        "temporary_keys": {
            "pattern": "temp:{type}:{user_id}:{resource_id}",
            "examples": [
                "temp:upload:user-123:file-abc",
                "temp:export:user-456:report-xyz",
                "temp:session:user-789:token-def"
            ]
        }
    }