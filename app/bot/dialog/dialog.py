from aiogram_dialog import Dialog
from app.bot.dialog.windows import get_nickname_window, get_age_window, get_gender_window, get_confirmed_windows

form_dialog = Dialog(
    get_nickname_window(),
    get_age_window(),
    get_gender_window(),
    get_confirmed_windows()
)
