import redis.asyncio as redis
from typing import Optional
from src.config import settings


class RedisService:
    """Redis connection service for background task management."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection."""
        if not self.redis:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if not self.redis:
            await self.connect()
        return self.redis


redis_service = RedisService()