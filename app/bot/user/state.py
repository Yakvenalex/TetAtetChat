from aiogram.fsm.state import StatesGroup, State


class AgeState(StatesGroup):
    age = State()


class NickState(StatesGroup):
    nickname = State()
