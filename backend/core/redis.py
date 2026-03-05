"""
Redis连接管理
"""
import redis.asyncio as redis
from .config import settings

# 创建Redis连接池
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """获取Redis客户端"""
    return redis.Redis(connection_pool=redis_pool)


class RedisClient:
    """Redis客户端封装"""

    def __init__(self):
        self.client = redis.Redis(connection_pool=redis_pool)

    async def set_cache(self, key: str, value: str, expire: int = 3600):
        """设置缓存"""
        await self.client.set(key, value, ex=expire)

    async def get_cache(self, key: str) -> str:
        """获取缓存"""
        return await self.client.get(key)

    async def delete_cache(self, key: str):
        """删除缓存"""
        await self.client.delete(key)

    async def push_task(self, queue: str, task: str):
        """推送任务到队列"""
        await self.client.rpush(queue, task)

    async def pop_task(self, queue: str, timeout: int = 0):
        """从队列获取任务"""
        if timeout > 0:
            return await self.client.blpop(queue, timeout=timeout)
        return await self.client.lpop(queue)

    async def close(self):
        """关闭连接"""
        await self.client.close()


redis_client = RedisClient()
