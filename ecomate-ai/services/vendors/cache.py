"""Vendor data caching implementation."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class VendorCache:
    """Simple in-memory cache with TTL support for vendor data"""
    
    def __init__(self, default_ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodically clean up expired cache entries"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if now > entry['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        entry = self.cache.get(key)
        if entry is None:
            return None
        
        if datetime.now() > entry['expires_at']:
            del self.cache[key]
            return None
        
        return entry['data']
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl_seconds or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            'data': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if now > entry['expires_at'])
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'cache_hit_ratio': getattr(self, '_hit_ratio', 0.0)
        }
    
    def __del__(self):
        """Cleanup when cache is destroyed"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

class RedisVendorCache(VendorCache):
    """Redis-based cache implementation (optional upgrade)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl_seconds: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl_seconds
        self.redis_client = None
        self._connected = False
    
    async def _ensure_connected(self):
        """Ensure Redis connection is established"""
        if not self._connected:
            try:
                import aioredis
                self.redis_client = aioredis.from_url(self.redis_url)
                await self.redis_client.ping()
                self._connected = True
                logger.info("Connected to Redis cache")
            except ImportError:
                logger.warning("aioredis not available, falling back to in-memory cache")
                super().__init__(self.default_ttl)
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}, falling back to in-memory cache")
                super().__init__(self.default_ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        await self._ensure_connected()
        
        if not self._connected:
            return await super().get(key)
        
        try:
            data = await self.redis_client.get(f"vendor:{key}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in Redis cache with TTL"""
        await self._ensure_connected()
        
        if not self._connected:
            return await super().set(key, value, ttl_seconds)
        
        try:
            ttl = ttl_seconds or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(f"vendor:{key}", ttl, serialized_value)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        await self._ensure_connected()
        
        if not self._connected:
            return await super().delete(key)
        
        try:
            result = await self.redis_client.delete(f"vendor:{key}")
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear(self) -> None:
        """Clear all vendor cache entries from Redis"""
        await self._ensure_connected()
        
        if not self._connected:
            return await super().clear()
        
        try:
            keys = await self.redis_client.keys("vendor:*")
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis clear error: {e}")

def create_cache(cache_type: str = "memory", **kwargs) -> VendorCache:
    """Factory function to create appropriate cache instance"""
    if cache_type == "redis":
        redis_url = kwargs.get("redis_url", os.getenv("REDIS_URL", "redis://localhost:6379"))
        return RedisVendorCache(redis_url, kwargs.get("default_ttl_seconds", 3600))
    else:
        return VendorCache(kwargs.get("default_ttl_seconds", 3600))