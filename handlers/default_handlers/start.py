from handlers.default_handlers.help import help_handler
from loader import bot
from loguru import logger
from telebot.types import Message


@logger.catch
@bot.message_handler(commands=['start'])
def start_message(message: Message) -> None:
    """
    Функция, которая выполняет команду /start
    """
    logger.info("User {user} used a command /start".format(user=message.chat.id))
    bot.send_message(chat_id=message.chat.id, text=f'Добрый день, {message.from_user.first_name}!')
    help_handler(message)
