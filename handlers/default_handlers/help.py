from loader import bot
from loguru import logger
from telebot.types import Message


@logger.catch
@bot.message_handler(commands=['help'])
def help_handler(message: Message) -> None:
    """
    Функция, которая выполняет команду /help
    """
    logger.info("User {user} used a command /help".format(user=message.chat.id))
    bot.send_message(chat_id=message.chat.id,
                     text='Вы можете управлять мной с помощью следующих команд:\n'
                          '/lowprice - узнать топ самых дешёвых отелей в городе\n'
                          '/highprice - узнать топ самых дорогих отелей в городе\n'
                          '/bestdeal - узнать топ отелей, наиболее подходящих по цене и расположению от центра'
                          '/history - узнать историю поиска отелей')
