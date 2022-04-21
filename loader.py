from telebot import TeleBot
from config_data import config
from loguru import logger

logger.add('log.log', format="{time} {level} {message}", level='INFO')
bot = TeleBot(token=config.BOT_TOKEN)
