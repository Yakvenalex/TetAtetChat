# Инициализируем бота и диспетчер
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram_dialog import setup_dialogs
from loguru import logger
from app.bot.dialog.dialog import form_dialog
from app.bot.user.router import router as user_router
from app.config import settings
from app.dao.database_middleware import DatabaseMiddlewareWithoutCommit, DatabaseMiddlewareWithCommit
from app.dao.create_db import create_users_table

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


async def set_commands():
    commands = [BotCommand(command='start', description='Рестарт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


# Функция, которая выполнится когда бот запустится
async def start_bot():
    await create_users_table()
    setup_dialogs(dp)
    dp.update.middleware.register(DatabaseMiddlewareWithoutCommit())
    dp.update.middleware.register(DatabaseMiddlewareWithCommit())
    await set_commands()
    dp.include_router(form_dialog)
    dp.include_router(user_router)

    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f'Я запущен🥳.')
        except:
            pass
    logger.info("Бот успешно запущен.")


# Функция, которая выполнится когда бот завершит свою работу
async def stop_bot():
    try:
        for admin_id in settings.ADMIN_IDS:
            await bot.send_message(admin_id, 'Бот остановлен. За что?😔')
    except:
        pass
    logger.error("Бот остановлен!")
