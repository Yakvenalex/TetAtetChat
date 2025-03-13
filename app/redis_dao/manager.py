from fastapi import Depends
from app.config import settings
from app.redis_dao.redis_client import RedisClient
from app.redis_dao.custom_redis import CustomRedis
from functools import wraps
from typing import Callable, Awaitable, Any
from loguru import logger


redis_manager = RedisClient(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    ssl_flag=settings.REDIS_SSL,
)


async def get_redis() -> CustomRedis:
    """Функция зависимости для получения клиента Redis"""
    return redis_manager.get_client()


def cached(cache_key: str, ttl: int = 1800):
    """
    Декоратор для кэширования результатов функции.

    Args:
        cache_key: Ключ для кэширования данных. Поддерживает форматирование строки с использованием параметров функции.
        ttl: Время жизни кэша в секундах (по умолчанию 30 минут).
    """

    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Форматируем ключ кэша, используя все доступные параметры
                formatted_key = cache_key.format(**kwargs)
            except KeyError as e:
                logger.error(f"Ошибка форматирования ключа кэша: {e}")
                # В случае ошибки форматирования возвращаем результат без кэширования
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Неожиданная ошибка при работе с кэшем: {e}")
                return await func(*args, **kwargs)

            try:
                redis = await get_redis()
                result = await redis.get_cached_data(
                    cache_key=formatted_key,
                    fetch_data_func=func,
                    ttl=ttl,
                    *args,
                    **kwargs,
                )
                if result is None:
                    logger.warning(
                        f"Получено пустое значение из кэша для ключа {formatted_key}"
                    )
                return result
            except Exception as e:
                logger.error(f"Ошибка при работе с Redis: {e}")
                # В случае ошибки Redis возвращаем результат без кэширования
                return await func(*args, **kwargs)

        return wrapper

    return decorator
