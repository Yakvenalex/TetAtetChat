from typing import Any
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from app.bot.kbs import main_user_kb
from app.bot.schemas import UserSchema
from app.dao.dao import UserDAO


async def cancel_logic(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await callback.answer("Заполнение анкеты остановлено!")
    await callback.message.answer("Вы отменили сценарий анкетирования. К сожалению, без этого действия вы не "
                                  "сможете пользоваться ботом. Пожалуйста нажмите на /dialog и ответьте на пару "
                                  "вопросов о себе.")


async def error_age(message: Message, dialog_: Any, manager: DialogManager, error_: ValueError):
    await message.answer("Возраст должен быть целым числом!")


async def process_gender(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await callback.answer("Пол установлен!")
    dialog_manager.dialog_data["gender"] = button.widget_id
    await dialog_manager.next()


async def on_confirmation(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await callback.answer("Приступаю к сохранению")
    session = dialog_manager.middleware_data.get("session_with_commit")
    user_id = callback.from_user.id
    user = UserSchema(id=user_id,
                      username=callback.from_user.username,
                      first_name=callback.from_user.first_name,
                      last_name=callback.from_user.last_name,
                      nickname=dialog_manager.dialog_data["nickname"],
                      gender=dialog_manager.dialog_data["gender"],
                      age=dialog_manager.dialog_data["age"])
    await UserDAO(session).add(user)
    text = "Спасибо, что ответили на все вопросы! Теперь вам доступен доступ к чату."
    await callback.message.answer(text, reply_markup=main_user_kb(user_id))
    await dialog_manager.done()
