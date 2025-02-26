from aiogram_dialog import DialogManager


async def get_confirmed_data(dialog_manager: DialogManager, **kwargs):
    """Получение заполненных пользователем данных."""
    gender = dialog_manager.dialog_data["gender"]
    dialog_manager.dialog_data["age"] = dialog_manager.find("age").get_value()
    dialog_manager.dialog_data["nickname"] = dialog_manager.find("nickname").get_value()

    gender_text = "мужской" if gender == "man" else "женский"

    text = f"""
<b>Пожалуйста, проверьте введенные данные:</b>

• 🏷 Никнейм: <i>{dialog_manager.dialog_data["nickname"]}</i>
• 🎂 Возраст: <i>{dialog_manager.dialog_data["age"]} лет</i>
• ⚧ Пол: <i>{gender_text}</i>

<b>Всё верно?</b> Если нет, вы можете вернуться назад и исправить информацию.
"""
    return {"confirmed_text": text}
