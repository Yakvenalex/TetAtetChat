from redis.asyncio import Redis
from loguru import logger
from typing import Optional


class RedisClient:
    """Класс для управления подключением к Redis с поддержкой явного и автоматического управления."""

    def __init__(self, host: str, port: int, ssl_flag: bool, ssl_cert_reqs: str = "none", password: str | None = None):
        self.host = host
        self.port = port
        self.password = password
        self.ssl_flag = ssl_flag
        self.ssl_cert_reqs = ssl_cert_reqs
        self._client: Optional[Redis] = None

    async def connect(self):
        """Создает и сохраняет подключение к Redis."""
        if self._client is None:
            try:
                self._client = Redis(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    ssl=self.ssl_flag,
                    ssl_cert_reqs=self.ssl_cert_reqs,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Проверяем подключение
                await self._client.ping()
                logger.info("Redis подключен успешно")
            except Exception as e:
                logger.error(f"Ошибка подключения к Redis: {e}")
                raise

    async def close(self):
        """Закрывает подключение к Redis."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis соединение закрыто")

    def get_client(self) -> Redis:
        """Возвращает объект клиента Redis."""
        if self._client is None:
            raise RuntimeError("Redis клиент не инициализирован. Проверьте lifespan.")
        return self._client

    async def __aenter__(self):
        """Поддерживает асинхронный контекстный менеджер."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Автоматически закрывает подключение при выходе из контекста."""
        await self.close()

    async def delete_key(self, key: str):
        """Удаляет ключ из Redis."""
        await self._client.delete(key)
        logger.info(f"Ключ {key} удален")

    async def delete_keys_by_prefix(self, prefix: str):
        """Удаляет ключи, начинающиеся с указанного префикса."""
        keys = await self._client.keys(prefix + '*')
        if keys:
            await self._client.delete(*keys)
            logger.info(f"Удалены ключи, начинающиеся с {prefix}")

    async def delete_all_keys(self):
        """Удаляет все ключи из текущей базы данных Redis."""
        await self._client.flushdb()
        logger.info("Удалены все ключи из текущей базы данных")

    async def get_value(self, key: str):
        """Возвращает значение ключа из Redis."""
        value = await self._client.get(key)
        if value:
            return value
        else:
            logger.info(f"Ключ {key} не найден")
            return None

    async def set_value(self, key: str, value: str):
        """Устанавливает значение ключа в Redis."""
        await self._client.set(key, value)
        logger.info(f"Установлено значение ключа {key}")

    async def set_value_with_ttl(self, key: str, value: str, ttl: int):
        """Устанавливает значение ключа с временем жизни в Redis."""
        await self._client.setex(key, ttl, value)
        logger.info(f"Установлено значение ключа {key} с TTL {ttl}")

    async def exists(self, key: str) -> bool:
        """Проверяет, существует ли ключ в Redis."""
        return await self._client.exists(key)

    async def get_keys(self, pattern: str = '*'):
        """Возвращает список ключей, соответствующих шаблону."""
        return await self._client.keys(pattern)
