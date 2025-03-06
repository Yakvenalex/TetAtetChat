from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.dialog.state import FormState
from app.bot.kbs import main_user_kb, profile_kb
from app.bot.schemas import UserIdSchema, NickSchema, AgeSchema
from app.dao.dao import UserDAO
from aiogram.fsm.state import StatesGroup, State


class AgeState(StatesGroup):
    age = State()


class NickState(StatesGroup):
    nickname = State()


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, dialog_manager: DialogManager,
                    session_without_commit: AsyncSession, state: FSMContext):
    await state.clear()
    user_info = await UserDAO(session_without_commit).find_one_or_none_by_id(message.from_user.id)
    if user_info is None:
        await dialog_manager.start(FormState.nickname, mode=StartMode.RESET_STACK)
    else:
        await message.answer("Вам открыт доступ к чату! Для работы воспользуйтесь клавиатурой ниже.",
                             reply_markup=main_user_kb(user_id=message.from_user.id,
                                                       sender=user_info.nickname))


@router.callback_query(F.data == "my_profile")
async def cmd_profile(call: CallbackQuery, session_without_commit: AsyncSession):
    await call.answer()
    user_info = await UserDAO(session_without_commit).find_one_or_none_by_id(call.from_user.id)

    gender_text = "👨 Мужской" if user_info.gender == "man" else "👩 Женский"

    profile_text = f"""
<b>👤 Ваш профиль в Тет-а-тет:</b>

• <b>🏷 Никнейм:</b> {user_info.nickname}
• <b>🎂 Возраст:</b> {user_info.age} лет / года
• <b>⚧ Пол:</b> {gender_text}
• <b>📛 Имя:</b> {user_info.first_name or 'Не указано'}
• <b>👥 Фамилия:</b> {user_info.last_name or 'Не указана'}
• <b>🆔 Имя пользователя:</b> {user_info.username or 'Не указано'}

✏️ Чтобы изменить данные, воспользуйтесь клавиатурой ниже.
"""

    await call.message.edit_text(profile_text, reply_markup=profile_kb(call.from_user.id, user_info.nickname))


@router.callback_query(F.data == "edit_nickname")
async def cmd_about(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("Укажите новый никнейм: ")
    await state.set_state(NickState.nickname)


@router.message(F.text, NickState.nickname)
async def cmd_edit_nickname(message: Message, state: FSMContext, session_with_commit: AsyncSession):
    user_dao = UserDAO(session_with_commit)
    await user_dao.update(filters=UserIdSchema(id=message.from_user.id),
                          values=NickSchema(nickname=message.text))
    await state.clear()
    await message.answer("Ваш никнейм изменен на: " + message.text,
                         reply_markup=main_user_kb(message.from_user.id, message.text))


@router.callback_query(F.data == "edit_age")
async def cmd_age(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("Укажите актуальный возраст: ")
    await state.set_state(AgeState.age)


@router.message(F.text, AgeState.age)
async def cmd_edit_age(message: Message, state: FSMContext, session_with_commit: AsyncSession):
    user_dao = UserDAO(session_with_commit)

    try:
        int(message.text)
        await user_dao.update(filters=UserIdSchema(id=message.from_user.id),
                              values=AgeSchema(age=int(message.text)))
        await state.clear()
        user_data = await user_dao.find_one_or_none_by_id(message.from_user.id)
        await message.answer("Ваш возраст изменен на: " + message.text,
                             reply_markup=main_user_kb(message.from_user.id, user_data.nicknmame))
    except ValueError:
        await message.edit_text("Введенное значение не является числом. Пожалуйста, введите число.")
        await state.set_state(AgeState.age)


@router.callback_query(F.data.startswith("about_us_"))
async def cmd_about(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    nickname = call.data.replace("about_us_", "")
    text = """
<b>Добро пожаловать в чат Тет-а-тет!</b>

Мы создали уникальное пространство для анонимного общения, где вы можете познакомиться и пообщаться с интересными людьми в формате один на один.

<b>Что мы предлагаем:</b>

• <i>Анонимность:</i> Ваша приватность - наш приоритет. Общайтесь свободно и безопасно.

• <i>Удобное меню:</i> Простой интерфейс с основными функциями всегда под рукой.

• <i>Гибкий профиль:</i> В разделе "Мой профиль" вы можете в любой момент изменить свои данные.

• <i>Мини-приложение:</i> Наше специальное мини-приложение для комфортного общения.

<b>Наша миссия</b> - создать комфортную среду для новых знакомств и увлекательных бесед. Мы верим, что каждый разговор может стать началом чего-то особенного.

Присоединяйтесь к Тет-а-тет и откройте для себя мир интересных собеседников!

<i>Приятного общения!</i>
"""

    await call.message.edit_text(text, reply_markup=main_user_kb(user_id, nickname))
