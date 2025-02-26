import os
from typing import List
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"
    DB_URL: str = 'sqlite+aiosqlite:///data/db.sqlite3'
    DB_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "db.sqlite3")
    BASE_URL: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_HOST: str

    @property
    def hook_url(self) -> str:
        """Возвращает URL вебхука"""
        return f"{self.BASE_URL}/webhook"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )


# Получаем параметры для загрузки переменных среды
settings = Settings()

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.txt")
logger.add(log_file_path, format=settings.FORMAT_LOG, level="INFO", rotation=settings.LOG_ROTATION)
