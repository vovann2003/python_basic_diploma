from datetime import datetime
import requests
import json
from loguru import logger
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from config_data import config
import re
from database.history_db.history_database import History
from user import *

RAPIDAPI_KEY = config.RAPID_API_KEY
headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': RAPIDAPI_KEY
}


def request_to_api(url: str, header: dict, querystring):
    try:
        response = requests.request("GET", url, headers=header, params=querystring, timeout=10)
        if response.status_code == requests.codes.ok:
            return response.text
    except Exception(requests.RequestException, TimeoutError) as ex:
        logger.error(f"Exception: {ex}")
        return None


def city_founding(destination: str):
    """
    Функция для поиска заданного пользователем направления
    """
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    querystring = {"query": destination, "locale": "ru_RU"}
    destinations = dict()
    response = request_to_api(url=url, header=headers, querystring=querystring)
    if not response:
        print('При поиске возникла ошибка! Попробуйте снова\n')
        return None
    else:
        suggestions = json.loads(response)["suggestions"][0]["entities"]
        if suggestions:
            for element in suggestions:
                caption = re.sub(r'<.+?>', '', element['caption'])
                destinationId = element['destinationId']
                destinations[int(destinationId)] = caption
            return destinations
        else:
            pass


@logger.catch
def hotel_info(destination_id: str, page_number: str, hotel_count: str,
               check_in: str, check_out: str, price_min: int or None, sort_order: str,
               price_max: int or None):
    """
    Функция, которая преобразовывает информацию об отеле в словарь
    """
    url = "https://hotels4.p.rapidapi.com/properties/list"
    querystring = {
        "destinationId": destination_id,
        "pageNumber": page_number,
        "checkIn": check_in,
        "checkOut": check_out,
        "adults1": "1",
        "priceMin": price_min,
        "priceMax": price_max,
        "sortOrder": sort_order,
        "locale": "ru_RU", "currency": "USD"
    }
    try:
        response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
        hotels_suggestions = response.json()['data']['body']['searchResults']['results'][:int(hotel_count)]
        for element in hotels_suggestions:
            hotels = dict()
            hotels['hotel_id'] = element['id']
            hotels['hotel_name'] = element['name']
            hotels['hotel_rating'] = element['starRating']
            address = element['address']
            hotels['hotel_address'] = address.get('streetAddress', ' ')
            hotels['hotel_locality'] = address.get('locality', ' ')
            hotels['hotel_distance_center'] = element['landmarks'][0]['distance']
            hotels['hotel_country'] = address.get('countryName', ' ')
            hotels['hotel_postal_code'] = address.get('postalCode', ' ')
            coordinate = element['coordinate']
            hotels['hotel_latitude'] = coordinate.get('lat', ' ')
            hotels['hotel_longitude'] = coordinate.get('lon', ' ')
            price = element['ratePlan']['price']
            hotels['hotel_price'] = price.get('exactCurrent', ' ')
            hotels['hotel_info'] = price.get('info', ' ')
            hotels['hotel_url'] = f'https://ua.hotels.com/ho{hotels["hotel_id"]}/' \
                                  f'?q-check-in={check_in}' \
                                  f'&q-check-out={check_out}' \
                                  f'&q-rooms=1&q-room-0-adults=2&q-room-0-children=0'
            yield hotels
    except requests.exceptions.ReadTimeout as exception:
        logger.info(f"Couldn't find hotel_info by destination_id {destination_id}: {exception}")
        return None


def photo_info(hotel_id: str, photo_amount: int):
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    querystring = {"id": hotel_id}
    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        hotel_photo = response.json()['hotelImages'][:int(photo_amount)]
        for photo in hotel_photo:
            url = re.sub(r'{size}', 'z', photo['baseUrl'])
            yield url
    except (IndexError, requests.ReadTimeout, KeyError) as ex:
        logger.error(f"Couldn't find hotel photo for hotel_id {hotel_id}: {ex}")
        return list()


def lowprice_highprice_command(user_id: int):
    """
    Функция, которая получает информацию из базы данных для команды /lowprice или /highprice
    """
    sort_order = None
    cur_user = User.get_user(user_id=user_id)
    command = cur_user.command
    city_id = cur_user.city_id
    check_in = cur_user.check_in
    check_out = cur_user.check_out
    hotels_count = cur_user.hotel_count
    photo_count = cur_user.photo_count
    if command == '/lowprice':
        sort_order = 'PRICE'
    elif command == '/highprice':
        sort_order = 'PRICE_HIGHEST_FIRST'
    result = hotel_info(destination_id=city_id, page_number='1', check_in=check_in, hotel_count=hotels_count,
                        check_out=check_out, price_min=None, price_max=None, sort_order=sort_order)
    if result is None:
        return None
    checks_in = str(check_in).split('-')
    checks_out = str(check_out).split('-')
    nights_count = int(checks_out[2]) - int(checks_in[2])
    hotel_text = ''
    for index, hotel in enumerate(result, start=1):
        keyboard = InlineKeyboardMarkup()
        button_1 = InlineKeyboardButton(url=hotel['hotel_url'], callback_data='yes', text='Забронировать')
        button_2 = InlineKeyboardButton(
            url=f"https://www.google.com.ua/maps/@{hotel['hotel_latitude']},{hotel['hotel_longitude']},20z?hl=ru",
            text='Карта')
        keyboard.add(button_1, button_2)
        one_night_price = hotel['hotel_price']
        total = round(int(one_night_price) * nights_count, 3)
        hotels_info = f"{index}) {hotel['hotel_name']}\n" \
                      f"Рейтинг: {hotel['hotel_rating']} \u2B50\n" \
                      f"Адрес: {hotel['hotel_country']}, {hotel['hotel_locality']}, {hotel['hotel_address']}\n" \
                      f"Расстояние до центра: {hotel['hotel_distance_center']}\n" \
                      f"Цена за одну ночь: ${one_night_price}\n" \
                      f"Цена за весь период: ${total}\n"
        hotel_text += hotels_info + '\n'
        photos = []
        if photo_count != 0:
            result = photo_info(hotel_id=hotel['hotel_id'], photo_amount=photo_count)
            for index_photo in result:
                result = InputMediaPhoto(index_photo)
                photos.append(result)
            yield keyboard, hotels_info, photos
        else:
            yield keyboard, hotels_info
    History.create(user_id=user_id, command=command, date_time=datetime.now(), hotels_info=hotel_text)


def bestdeal_command(user_id: int):
    cur_user = User.get_user(user_id=user_id)
    price_min = cur_user.price_min
    price_max = cur_user.price_max
    city_id = cur_user.city_id
    check_in = cur_user.check_in
    check_out = cur_user.check_out
    hotels_amount = cur_user.hotel_count
    photo_count = cur_user.photo_count
    distance_min = cur_user.distance_min
    distance_max = cur_user.distance_max

    result = hotel_info(destination_id=city_id, page_number='1', check_in=check_in, hotel_count=str(hotels_amount),
                        check_out=check_out, price_min=price_min, price_max=price_max,
                        sort_order='DISTANCE_FROM_LANDMARK')  # TODO Подскажите как продолжить поиск по другим страницам, если не нашлись отели на 1 странице?
    if result is None:
        return None
    checks_in = str(check_in).split('-')
    checks_out = str(check_out).split('-')
    nights_count = int(checks_out[2]) - int(checks_in[2])
    hotel_text = ''
    for index, hotel in enumerate(result, start=1):
        keyboard = InlineKeyboardMarkup()
        button_1 = InlineKeyboardButton(url=hotel['hotel_url'], callback_data='yes', text='Забронировать')
        button_2 = InlineKeyboardButton(
            url=f"https://www.google.com.ua/maps/@{hotel['hotel_latitude']},{hotel['hotel_longitude']},20z?hl=ru",
            text='Карта')
        keyboard.add(button_1, button_2)
        if hotels_amount == 0:
            break
        distance = float(hotel['hotel_distance_center'].split()[0].split(',')[0])
        if not int(distance_min) <= distance <= int(distance_max):
            one_night_price = hotel['hotel_price']
            total = round(int(one_night_price) * nights_count, 3)
            hotels_info = f"{index}) {hotel['hotel_name']}\n" \
                          f"Рейтинг: {hotel['hotel_rating']} \u2B50\n" \
                          f"Адрес: {hotel['hotel_country']}, {hotel['hotel_locality']}, {hotel['hotel_address']}\n" \
                          f"Расстояние до центра: {hotel['hotel_distance_center']}\n" \
                          f"Цена за одну ночь: ${one_night_price}\n" \
                          f"Цена за весь период: ${total}\n"
            hotel_text += hotels_info + '\n'
            photos = []
            if photo_count != 0:
                result = photo_info(hotel_id=hotel['hotel_id'], photo_amount=photo_count)
                for index_photo in result:
                    result = InputMediaPhoto(index_photo)
                    photos.append(result)
                yield keyboard, hotels_info, photos
            else:
                yield keyboard, hotels_info
    History.create(user_id=user_id, command='/bestdeal', date_time=datetime.now(), hotels_info=hotel_text)
