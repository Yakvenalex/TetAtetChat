from contextlib import asynccontextmanager
from app.bot.create_bot import dp, start_bot, bot, stop_bot
from app.config import settings
from aiogram.types import Update
from fastapi import FastAPI, Request
from loguru import logger

from app.redis_config import test_redis_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Бот запущен...")
    await test_redis_connection()
    await start_bot()
    webhook_url = settings.hook_url
    await bot.set_webhook(url=webhook_url,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    logger.success(f"Вебхук установлен: {webhook_url}")
    yield
    logger.info("Бот остановлен...")
    await stop_bot()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request) -> None:
    logger.info("Получен запрос с вебхука.")
    try:
        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        logger.info("Обновление успешно обработано.")
    except Exception as e:
        logger.error(f"Ошибка при обработке обновления с вебхука: {e}")
