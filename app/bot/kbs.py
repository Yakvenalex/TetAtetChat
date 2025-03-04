from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config import settings


def main_user_kb(user_id: int = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="👤 Мой профиль", callback_data="my_profile")
    kb.button(text="ℹ️ О нас", callback_data="about_us")
    kb.button(text="💬 Чат Тет-а-тет", web_app=WebAppInfo(url=settings.FRONT_URL))

    kb.adjust(1)
    return kb.as_markup()


def profile_kb():
    kb = InlineKeyboardBuilder()

    kb.button(text="Изменить никнейм", callback_data="edit_nickname")
    kb.button(text="Изменить возраст", callback_data="edit_age")
    kb.button(text="ℹ️ О нас", callback_data="about_us")
    kb.button(text="💬 Чат Тет-а-тет", web_app=WebAppInfo(url=settings.FRONT_URL))

    kb.adjust(1)
    return kb.as_markup()