from peewee import *

db = SqliteDatabase(database='user_history.db')


class History(Model):
    """
    Класс История. Заполняет в БД информацию о командах и отелях пользователя для команды /history
    """
    user_id = CharField()
    command = CharField()
    date_time = CharField()
    hotels_info = CharField()

    class Meta:
        database = db
        primary_key = False


with db:
    History.create_table()
