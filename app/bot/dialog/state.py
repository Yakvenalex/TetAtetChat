from aiogram.fsm.state import StatesGroup, State


class FormState(StatesGroup):
    nickname = State()
    gender = State()
    age = State()
    confirmation = State()
