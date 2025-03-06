from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config import settings


def main_user_kb(user_id: int, sender: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="👤 Мой профиль", callback_data="my_profile")
    kb.button(text="ℹ️ О нас", callback_data=f"about_us_{sender}")
    url = f"{settings.FRONT_URL}?user_id={user_id}&sender={sender}"
    kb.button(text="💬 Чат Тет-а-тет", web_app=WebAppInfo(url=url))

    kb.adjust(1)
    return kb.as_markup()


def profile_kb(user_id: int, sender: str):
    kb = InlineKeyboardBuilder()

    kb.button(text="Изменить никнейм", callback_data="edit_nickname")
    kb.button(text="Изменить возраст", callback_data="edit_age")
    kb.button(text="ℹ️ О нас", callback_data="about_us")
    url = f"{settings.FRONT_URL}?user_id={user_id}&sender={sender}"
    kb.button(text="💬 Чат Тет-а-тет", web_app=WebAppInfo(url=url))

    kb.adjust(1)
    return kb.as_markup()