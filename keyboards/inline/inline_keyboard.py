from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def city_keyboard(city_list: dict) -> InlineKeyboardMarkup:
    """
    Функция которая создаёт inline кнопки для городов и выводит пользователю
    """
    inline_keyboard = InlineKeyboardMarkup(row_width=3)
    for city_id, index_city in city_list.items():
        inline_button = InlineKeyboardButton(text=index_city, callback_data=city_id)
        inline_keyboard.add(inline_button)
    inline_button = InlineKeyboardButton(text='Выбрать другой город: ', callback_data='777')
    inline_keyboard.add(inline_button)
    return inline_keyboard
