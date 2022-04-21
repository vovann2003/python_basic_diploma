from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def hotel_count_keyboard() -> ReplyKeyboardMarkup:
    """
    Функция которая создаёт кнопки для ввода пользователем количества отелей
    """
    keyboard = ReplyKeyboardMarkup(row_width=5)
    buttons = []
    for index_button in range(1, 11):
        button = KeyboardButton(str(index_button))
        buttons.append(button)
    keyboard.add(*buttons)
    return keyboard


def photo_answer_keyboard() -> ReplyKeyboardMarkup:
    """
    Функция создаёт клавиатуру с вариантами ответов для вывода фотографий
    """
    keyboard = ReplyKeyboardMarkup(row_width=1)
    button_1 = KeyboardButton(text='да')
    button_2 = KeyboardButton(text='нет')
    keyboard.add(button_1, button_2)
    return keyboard


def photo_count_keyboard() -> ReplyKeyboardMarkup:
    """
    Функция создаёт варианты с выводом количества отелей
    """
    keyboard = ReplyKeyboardMarkup()
    buttons = []
    for index_button in range(1, 11):
        button = KeyboardButton(text=str(index_button))
        buttons.append(button)
    keyboard.add(*buttons)
    return keyboard
