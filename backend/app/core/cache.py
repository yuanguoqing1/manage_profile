"""
缓存管理器模块
提供统一的Redis缓存操作接口
"""
from typing import Optional
import json
import redis.asyncio as redis
from app.core.config import settings


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        """
        初始化缓存管理器
        
        Args:
            redis_client: Redis客户端实例
        """
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[str]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在返回None
        """
        try:
            value = await self.redis.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            # 缓存失败不应该影响主流程
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = 300):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认300秒（5分钟）
        """
        try:
            await self.redis.setex(key, ttl, value)
        except Exception as e:
            # 缓存失败不应该影响主流程
            print(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """
        删除缓存
        
        Args:
            key: 缓存键
        """
        try:
            await self.redis.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            **kwargs: 键值对参数
            
        Returns:
            生成的缓存键
        """
        parts = [prefix]
        for key in sorted(kwargs.keys()):
            parts.append(f"{key}:{kwargs[key]}")
        return ":".join(parts)
