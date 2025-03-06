import json
from loguru import logger
from app.config import settings
from app.redis_dao.redis_client import RedisClient
from redis.asyncio import Redis

redis_manager = RedisClient(host=settings.REDIS_HOST,
                            port=settings.REDIS_PORT,
                            password=settings.REDIS_PASSWORD,
                            ssl_flag=settings.REDIS_SSL)


async def get_redis() -> Redis:
    """Функция зависимости для получения клиента Redis"""
    return redis_manager.get_client()


async def get_cached_data(redis_client: Redis, cache_key: str, fetch_data_func, *args, **kwargs):
    """
    Получает данные из кэша Redis или из БД, если их нет в кэше.
    """
    cached_data = await redis_client.get(cache_key)

    if cached_data:
        logger.info("Беру с кэша")
        return json.loads(cached_data)
    else:
        logger.info("Помещаю в кэш")
        data = await fetch_data_func(*args, **kwargs)

        # Сохраняем данные в кэше с временем жизни 30 минут
        await redis_client.setex(cache_key, 1800, json.dumps(data))

        return data
