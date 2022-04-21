from peewee import *

db = SqliteDatabase(database='user.db')


class Users(Model):
    """
    Класс, который заполняет информацию в БД о поисках пользователя
    """
    user_id = CharField()
    command = CharField(null=True)
    city_id = CharField(null=True)
    price_min = CharField(null=True)
    price_max = CharField(null=True)
    check_in = CharField(null=True)
    check_out = CharField(null=True)
    distance_min = CharField(null=True)
    distance_max = CharField(null=True)
    hotel_count = CharField(null=True)
    photo_count = CharField(null=True)

    class Meta:
        database = db


with db:
    Users.create_table()
