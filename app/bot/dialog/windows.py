from aiogram_dialog import Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Next, Cancel, Group, Button, Back
from aiogram_dialog.widgets.text import Const, Format
from app.bot.dialog.getters import get_confirmed_data
from app.bot.dialog.handlers import cancel_logic, error_age, process_gender, on_confirmation
from app.bot.dialog.state import FormState


def get_nickname_window() -> Window:
    """Окно для ввода никнейма пользователя."""
    return Window(
        Const("Давайте знакомиться! Ответьте на пару вопросов о себе. Для начала укажите имя, "
              "которое будут видеть пользователи чата Тет-А-Тет:"),
        TextInput(
            id="nickname",
            on_success=Next(),
            type_factory=str,
        ),
        Cancel(Const("Отмена"), on_click=cancel_logic),
        state=FormState.nickname
    )


def get_age_window():
    return Window(
        Const("Укажите свой возраст:"),
        TextInput(
            id="age",
            on_error=error_age,
            on_success=Next(),
            type_factory=int,
        ),
        Back(Const("Назад")),
        Cancel(Const("Отмена"), on_click=cancel_logic),
        state=FormState.age,
    )


def get_gender_window():
    return Window(
        Const("Выберите пол"),
        Group(
            Button(text=Const("Мужской"), id="man", on_click=process_gender),
            Button(text=Const("Женский"), id="woman", on_click=process_gender),
            width=2
        ),
        Back(Const("Назад")),
        Cancel(Const("Отмена"), on_click=cancel_logic),
        state=FormState.gender
    )


def get_confirmed_windows():
    return Window(
        Format("{confirmed_text}"),
        Group(
            Button(Const("Все верно"), id="confirm", on_click=on_confirmation),
            Back(Const("Назад")),
            Cancel(Const("Отмена"), on_click=cancel_logic),
        ),
        state=FormState.confirmation,
        getter=get_confirmed_data
    )
