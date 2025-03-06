from functools import lru_cache
import redis.asyncio as redis
from loguru import logger
from redis.exceptions import RedisError, ConnectionError
from app.config import settings


# Фабрика для создания Redis клиента
@lru_cache()
def get_redis_client():
    try:
        return redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            ssl=True,
            ssl_cert_reqs="none",
            decode_responses=True,  # Добавлено для удобства работы
            socket_timeout=5,  # Таймаут операций
            socket_connect_timeout=5,  # Таймаут подключения
            retry_on_timeout=True,  # Автоматический реконнект
            max_connections=10  # Максимальное число подключений
        )
    except Exception as e:
        logger.error(f"Ошибка создания Redis-клиента: {e}")
        raise


# Зависимость для получения Redis клиента
async def get_redis_db():
    client = get_redis_client()
    try:
        # Проверка соединения перед использованием
        await client.ping()
        async with client as redis_client:
            yield redis_client
    except (RedisError, ConnectionError) as e:
        logger.error(f"Ошибка подключения к Redis: {e}")
        raise
    finally:
        # Закрытие соединения
        await client.aclose()


# Асинхронная функция для подключения к Redis
async def test_redis_connection():
    # Подключение к Redis через контекстный менеджер
    client = get_redis_client()
    async with client as r:
        # Проверка подключения
        try:
            # Попытка выполнить команду PING
            response = await r.ping()
            if response:
                logger.success("Подключение к Redis успешно!")
            else:
                logger.warning("Не удалось подключиться к Redis.")
        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
