import json
from redis.asyncio import Redis
from loguru import logger
from typing import Any, Callable, Awaitable


class CustomRedis(Redis):
    """Расширенный класс Redis с дополнительными методами"""

    async def delete_key(self, key: str):
        """Удаляет ключ из Redis."""
        await self.delete(key)
        logger.info(f"Ключ {key} удален")

    async def delete_keys_by_prefix(self, prefix: str):
        """Удаляет ключи, начинающиеся с указанного префикса."""
        keys = await self.keys(prefix + '*')
        if keys:
            await self.delete(*keys)
            logger.info(f"Удалены ключи, начинающиеся с {prefix}")

    async def delete_all_keys(self):
        """Удаляет все ключи из текущей базы данных Redis."""
        await self.flushdb()
        logger.info("Удалены все ключи из текущей базы данных")

    async def get_value(self, key: str):
        """Возвращает значение ключа из Redis."""
        value = await self.get(key)
        if value:
            return value
        else:
            logger.info(f"Ключ {key} не найден")
            return None

    async def set_value(self, key: str, value: str):
        """Устанавливает значение ключа в Redis."""
        await self.set(key, value)
        logger.info(f"Установлено значение ключа {key}")

    async def set_value_with_ttl(self, key: str, value: str, ttl: int):
        """Устанавливает значение ключа с временем жизни в Redis."""
        await self.setex(key, ttl, value)
        logger.info(f"Установлено значение ключа {key} с TTL {ttl}")

    async def exists(self, key: str) -> bool:
        """Проверяет, существует ли ключ в Redis."""
        return await super().exists(key)

    async def get_keys(self, pattern: str = '*'):
        """Возвращает список ключей, соответствующих шаблону."""
        return await self.keys(pattern)

    async def get_cached_data(
        self,
        cache_key: str,
        fetch_data_func: Callable[..., Awaitable[Any]],
        *args,
        ttl: int = 1800,
        **kwargs
    ) -> Any:
        """
        Получает данные из кэша Redis или из БД, если их нет в кэше.

        Args:
            cache_key: Ключ для кэширования данных
            fetch_data_func: Асинхронная функция для получения данных из БД
            *args: Позиционные аргументы для fetch_data_func
            ttl: Время жизни кэша в секундах (по умолчанию 30 минут)
            **kwargs: Именованные аргументы для fetch_data_func

        Returns:
            Данные из кэша или из БД
        """
        cached_data = await self.get(cache_key)

        if cached_data:
            logger.info(f"Данные получены из кэша для ключа: {cache_key}")
            return json.loads(cached_data)
        else:
            logger.info(f"Данные не найдены в кэше для ключа: {cache_key}, получаем из источника")
            data = await fetch_data_func(*args, **kwargs)

            # Преобразуем данные в зависимости от их типа
            if isinstance(data, list):
                processed_data = [
                    item.to_dict() if hasattr(item, 'to_dict') else item 
                    for item in data
                ]
            else:
                processed_data = data.to_dict() if hasattr(data, 'to_dict') else data

            # Сохраняем данные в кэше с указанным временем жизни
            await self.setex(cache_key, ttl, json.dumps(processed_data))
            logger.info(f"Данные сохранены в кэш для ключа: {cache_key} с TTL: {ttl} сек")

            return processed_data