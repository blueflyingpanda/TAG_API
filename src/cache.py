import logging

from redis.asyncio import ConnectionPool, Redis

from conf import settings

redis_pool: ConnectionPool | None = None


logger = logging.getLogger('cache')


async def get_cache() -> Redis:
    """Get Redis client from pool"""
    return Redis(connection_pool=redis_pool, decode_responses=True)


async def init_cache():
    """Initialize Redis connection pool"""
    global redis_pool
    redis_pool = ConnectionPool(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_name,
        password=settings.redis_pass,
        max_connections=5,
        decode_responses=True,
        encoding='utf-8',
    )

    # Test connection
    redis = Redis(connection_pool=redis_pool)
    await redis.ping()
    await redis.close()
    logger.info('✅ Redis pool initialized')


async def close_cache():
    """Close Redis pool"""
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()
        logger.info('❌ Redis pool closed')
