class User:
    users = dict()

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.command = ''
        self.city_id = None
        self.price_min = 0
        self.price_max = 0
        self.check_in = None
        self.check_out = None
        self.distance_min = 0
        self.distance_max = 0
        self.hotel_count = 0
        self.photo_count = 0

        User.add_user(user_id, self)

    @classmethod
    def add_user(cls, user_id: int, user: 'User') -> None:
        cls.users[user_id] = user

    @classmethod
    def get_user(cls, user_id: int):
        if user_id in cls.users:
            return cls.users[user_id]
        else:
            return User(user_id)
