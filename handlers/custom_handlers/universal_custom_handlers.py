from datetime import date, datetime
import telebot
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from database.users_db.user_database import Users
from handlers.default_handlers.help import help_handler
from keyboards.inline.inline_keyboard import city_keyboard
from keyboards.reply.reply_keyboard import hotel_count_keyboard, photo_answer_keyboard, photo_count_keyboard
from loader import bot
from loguru import logger
from telebot.types import Message, CallbackQuery
from rapidapi import city_founding, lowprice_highprice_command, bestdeal_command
from user import User
import re


@logger.catch
@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def start(message: Message) -> None:
    """
    Функция, которая выполняет команду /lowprice, /highprice или /bestdeal
    """
    logger.info("User {user} used a command {command}".format(user=message.chat.id, command=message.text))
    cur_user = User.get_user(user_id=message.chat.id)
    cur_user.command = message.text
    bot.send_message(chat_id=message.chat.id, text='В какой город вы хотите поехать?')
    bot.register_next_step_handler(message=message, callback=city_markup)


@logger.catch
def city_markup(message: Message) -> None:
    """
    Функция, которая выводит кнопки с вариантами городов
    """
    city = message.text
    cities = city_founding(city)
    inline_keyboard = city_keyboard(city_list=cities)
    bot.send_message(chat_id=message.from_user.id, text='Уточните, пожалуйста: ', reply_markup=inline_keyboard)


@logger.catch
@bot.callback_query_handler(func=lambda call: re.fullmatch(r'\d{3,}', call.data))
def city_callback_query(cal: CallbackQuery) -> None:
    """
    Функция для обработки id указанного города
    """
    if cal.data == '777':
        bot.send_message(chat_id=cal.message.chat.id, text='В какой город вы хотите поехать?')
        bot.register_next_step_handler(message=cal.message, callback=city_markup)
        return
    cur_user = User.get_user(user_id=cal.message.chat.id)
    cur_user.city_id = cal.data
    command = cur_user.command
    bot.edit_message_text(chat_id=cal.message.chat.id, message_id=cal.message.message_id, text=f'Город выбран')
    if command == '/lowprice' or command == '/highprice':
        new_message = bot.send_message(chat_id=cal.message.chat.id, text='Выберите дату заезда')
        create_check_in(message=new_message)
    else:
        new_message = bot.send_message(chat_id=cal.message.chat.id,
                                       text='Укажите диапозон цен через пробел(минимум и максимум)\n'
                                            'например 500 1000')
        bot.register_next_step_handler(message=new_message, callback=get_price_range)


@logger.catch
def get_price_range(message: Message) -> None:
    """
    Функция принимает диапозон цен(минимальное и максимальное значение) для команды /bestdeal
    """
    if re.fullmatch(r'\d+\s\d+', message.text):
        price = message.text.split()
        minimal_price = price[0]
        maximal_price = price[1]
        if int(minimal_price) > int(maximal_price):
            maximal_price, minimal_price = minimal_price, minimal_price
        cur_user = User.get_user(user_id=message.chat.id)
        cur_user.price_min = minimal_price
        cur_user.price_max = maximal_price
        new_message = bot.send_message(chat_id=message.chat.id,
                                       text='Введите диапозон расстояния(через пробел), на котором находится отель от центра\n'
                                            'например: 2 10\n')
        bot.register_next_step_handler(message=new_message, callback=get_distance_range)
    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Неверно введены данные\nУкажите диапозон цен через пробел(минимум и максимум)\n'
                              'например 500 1000')
        bot.register_next_step_handler(message=message, callback=get_price_range)


@logger.catch
def get_distance_range(message: Message) -> None:
    """
    Функция принимает диапозон расстояния, на котором находиться отель от центра для команды /bestdeal
    """
    if re.fullmatch(r'\d+\s\d+', message.text):
        distance = message.text.split()
        minimal_distance = distance[0]
        maximal_distance = distance[1]
        if int(minimal_distance) > int(maximal_distance):
            maximal_distance, minimal_distance = minimal_distance, maximal_distance
        cur_user = User.get_user(user_id=message.chat.id)
        cur_user.distance_min = minimal_distance
        cur_user.distance_max = maximal_distance
        bot.send_message(chat_id=message.chat.id, text='Выберите дату заезда')
        create_check_in(message)
    else:
        new_message = bot.send_message(chat_id=message.chat.id,
                                       text='Неверно введены данные\nВведите диапозон расстояния(через пробел), на котором находится отель от центра\n'
                                            'например: 2 10')
        bot.register_next_step_handler(message=new_message, callback=get_distance_range)


@logger.catch
def create_check_in(message: Message) -> None:
    """
    Функция создаёт кадендарь для даты заезда
    """
    calendar, step = DetailedTelegramCalendar(calendar_id='in',
                                              locale='ru',
                                              min_date=date.today(),
                                              max_date=date(2024, 3, 31)).build()
    bot.send_message(chat_id=message.chat.id,
                     text=f'Select {LSTEP[step]}',
                     reply_markup=calendar)


@logger.catch
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id='in'))
def callback_check_in(cal: CallbackQuery) -> None:
    """
    Функция обрабатывает дату заезда по календарю
    """
    result, key, step = DetailedTelegramCalendar(calendar_id='in',
                                                 locale='ru',
                                                 min_date=date.today(),
                                                 max_date=date(2024, 3, 31)).process(call_data=cal.data)
    if not result and key:
        bot.edit_message_text(f'Select {LSTEP[step]}',
                              chat_id=cal.message.chat.id,
                              message_id=cal.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"Дата заезда: {result}",
                              chat_id=cal.message.chat.id,
                              message_id=cal.message.message_id)
        cur_user = User.get_user(user_id=cal.message.chat.id)
        cur_user.check_in = result
        logger.info(f"User {cal.message.chat.id} selected a check-in date: {result}")
        new_message = bot.send_message(chat_id=cal.message.chat.id, text='Выберите дату выезда')
        create_check_out(message=new_message)


@logger.catch
def create_check_out(message: Message) -> None:
    """
    Функция создаёт кадендарь для даты выезда
    """
    cur_user = User.get_user(user_id=message.chat.id)
    check_in_date = cur_user.check_in
    current_date = datetime.strptime(str(check_in_date), '%Y-%m-%d').date()
    calendar, step = DetailedTelegramCalendar(calendar_id='out',
                                              locale='ru',
                                              min_date=date(current_date.year, current_date.month, current_date.day + 1),
                                              max_date=date(2024, 3, 31)).build()
    bot.send_message(chat_id=message.chat.id,
                     text=f'Select {LSTEP[step]}',
                     reply_markup=calendar)


@logger.catch
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id='out'))
def callback_check_out(cal: CallbackQuery) -> None:
    """
    Функция обрабатывает дату выезда по календарю
    """
    cur_user = User.get_user(user_id=cal.message.chat.id)
    check_in_date = cur_user.check_in
    current_date = datetime.strptime(str(check_in_date), '%Y-%m-%d').date()
    result, key, step = DetailedTelegramCalendar(calendar_id='out',
                                                 locale='ru',
                                                 min_date=date(current_date.year, current_date.month, current_date.day + 1),
                                                 max_date=date(2024, 3, 31)).process(call_data=cal.data)
    if not result and key:
        bot.edit_message_text(f'Select {LSTEP[step]}',
                              chat_id=cal.message.chat.id,
                              message_id=cal.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"Дата выезда: {result}",
                              chat_id=cal.message.chat.id,
                              message_id=cal.message.message_id)
        cur_user.check_out = result
        logger.info(f"User {cal.message.chat.id} selected a check-out date: {result}")
        keyboard = hotel_count_keyboard()
        new_message = bot.send_message(chat_id=cal.message.chat.id,
                                       text='Укажите сколько вы хотите вывести отелей(не больше 10)',
                                       reply_markup=keyboard)
        bot.register_next_step_handler(message=new_message, callback=hotels_count)


@logger.catch
def hotels_count(message: Message) -> None:
    """
    Функция принимает на вход количетсво отелей и проверяет на корректность
    """
    if not message.text.isdigit():
        bot.send_message(chat_id=message.chat.id,
                         text='Некорректный ввод! Введите цифру от 1 до 10')
        logger.info(f"User {message.chat.id} entered incorrect number of hotels: {message.text}")
        bot.register_next_step_handler(message=message, callback=hotels_count)
        return
    if int(message.text) <= 0 or int(message.text) > 10:
        bot.send_message(chat_id=message.chat.id,
                         text='Неверный ввод! Введите цифру от 1 до 10')
        logger.info(f"User {message.chat.id} entered incorrect number of hotels: {message.text}")
        bot.register_next_step_handler(message=message, callback=hotels_count)
    else:
        bot.send_message(chat_id=message.chat.id, text=f'Количество отелей: {message.text}', reply_markup=None)
        logger.info(f"User {message.chat.id} selected {message.text} hotel(s)")
        cur_user = User.get_user(user_id=message.chat.id)
        cur_user.hotel_count = message.text
        keyboard = photo_answer_keyboard()
        new_message = bot.send_message(chat_id=message.chat.id,
                                       text='Вывести фотографии?',
                                       reply_markup=keyboard)
        bot.register_next_step_handler(message=new_message, callback=check_hotel_photo)


@logger.catch
def check_hotel_photo(message: Message) -> None:
    """
    Функция обрабатывает ответ пользователя выводить фотографии или нет. Если да, то сколько?
    """
    response = message.text.lower()
    if response == 'да':
        bot.send_message(text='Хорошо', chat_id=message.chat.id, reply_markup=None)
        keyboard = photo_count_keyboard()
        new_message = bot.send_message(chat_id=message.chat.id,
                                       text='Укажите количество фотографий(не больше 10)',
                                       reply_markup=keyboard)
        bot.register_next_step_handler(message=new_message, callback=photo_count)
    elif response == 'нет':
        bot.send_message(chat_id=message.chat.id, text='Выполняется поиск \u23F3')
        cur_user = User.get_user(user_id=message.chat.id)
        cur_user.photo_count = 0
        print_info(message=message)
    else:
        new_message = bot.send_message(chat_id=message.chat.id, text='Некорректный ввод! Выберите да или нет')
        bot.register_next_step_handler(message=new_message, callback=check_hotel_photo)


@logger.catch
def photo_count(message: Message) -> None:
    """
    Функция котрая получает количество фотографий и проверяет корректность ввода
    """
    photos_amount = message.text
    if not photos_amount.isdigit():
        bot.send_message(chat_id=message.chat.id, text='Я вас не понимаю! Укажите количество фотографий числом')
        logger.info(f'User {message.chat.id} entered incorrect number of photos: {message.text}')
        bot.register_next_step_handler(message=message, callback=photo_count)
        return
    elif int(photos_amount) < 1 or int(photos_amount) > 10:
        bot.send_message(chat_id=message.chat.id,
                         text='Количество фотографий не должно быть меньше 1 или превышать 10!')
        logger.info(f'User {message.chat.id} entered incorrect number of photos: {message.text}')
        bot.send_message(chat_id=message.chat.id, text='Укажите количество фотографий(не больше 10)')
        bot.register_next_step_handler(message=message, callback=photo_count)
        return
    bot.send_message(chat_id=message.chat.id, text=f'Количество фотографий: {photos_amount}', reply_markup=None)
    logger.info(f"User {message.chat.id} selected {message.text} photo(s)")
    bot.send_message(chat_id=message.chat.id, text='Выполняется поиск \u23F3')
    cur_user = User.get_user(user_id=message.chat.id)
    cur_user.photo_count = int(photos_amount)
    print_info(message)


@logger.catch
def print_info(message: Message) -> None:
    """
    Функция выводит результат поиска отелей пользователю
    """
    cur_user = User.get_user(user_id=message.chat.id)
    command = cur_user.command
    if command == '/lowprice' or command == '/highprice':
        result = lowprice_highprice_command(user_id=message.chat.id)
    else:
        result = bestdeal_command(user_id=message.chat.id)
    photo_result = cur_user.photo_count
    if photo_result != 0:
        for keyboard, hotel, photo in result:
            try:
                bot.send_media_group(chat_id=message.chat.id, media=photo)
                bot.send_message(chat_id=message.chat.id,
                                 text=hotel,
                                 disable_web_page_preview=True,
                                 reply_markup=keyboard)
            except telebot.apihelper.ApiTelegramException:
                pass
    else:
        for keyboard, hotel in result:
            try:
                bot.send_message(chat_id=message.chat.id,
                                 text=hotel,
                                 reply_markup=keyboard)
            except telebot.apihelper.ApiTelegramException:
                pass
    Users.create(user_id=cur_user.user_id, command=cur_user.command, city_id=cur_user.city_id,
                 price_min=cur_user.price_min, price_max=cur_user.price_max,
                 check_in=cur_user.check_in, check_out=cur_user.check_out, distance_min=cur_user.distance_min,
                 distance_max=cur_user.distance_max, hotel_count=cur_user.hotel_count,
                 photo_count=cur_user.photo_count).save()
    keyboard = photo_answer_keyboard()
    new_message = bot.send_message(chat_id=message.chat.id, text='Поиск отелей заверешен! Хотите продолжить поиск?', reply_markup=keyboard)
    bot.register_next_step_handler(message=new_message, callback=restart)


@logger.catch
def restart(message: Message) -> None:
    response = message.text.lower()
    if response == 'да':
        help_handler(message)
    elif response == 'нет':
        bot.send_message(chat_id=message.chat.id, text=f"{message.from_user.first_name}, до скорых встреч!", reply_markup=None)
