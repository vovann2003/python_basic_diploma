from database.history_db.history_database import History
from loader import bot
from loguru import logger
from telebot.types import Message


@logger.catch
@bot.message_handler(commands=['history'])
def history(message: Message) -> None:
    """
    Функция которая выводит последние запросы поиска пользователя
    """
    logger.info("User {user} used a command {command}".format(user=message.chat.id, command=message.text))
    history_info = History.select().where(History.user_id == message.chat.id).order_by(History.date_time.asc())
    for figure in history_info:
        bot.send_message(chat_id=message.chat.id, text=f'Команда: {figure.command}\n'
                                                       f'Время: {figure.date_time}\n'
                                                       f'Информация:\n {figure.hotels_info}\n')
