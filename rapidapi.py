from datetime import datetime
import requests
import json
from loguru import logger
from telebot.types import InputMediaPhoto
from config_data import config
import re
from database.history_db.history_database import History
from keyboards.inline.inline_keyboard import hotel_keyboard
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
    try:
        suggestions = json.loads(response)["suggestions"][0]["entities"]
        if suggestions:
            for element in suggestions:
                caption = re.sub(r'<.+?>', '', element['caption'])
                destinationId = element['destinationId']
                destinations[int(destinationId)] = caption
            return destinations
    except (requests.exceptions.ReadTimeout, IndexError) as ex:
        logger.error(f"Couldn't find destinations for {destination}: {ex}")


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
            hotels['hotel_url'] = f"""https://ua.hotels.com/ho{hotels["hotel_id"]}/
                                      ?q-check-in={check_in}&q-check-out={check_out}
                                      &q-rooms=1&q-room-0-adults=2&q-room-0-children=0 """
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


def lowprice_highprice_command(user_id: int) -> dict or None:
    """
    Функция для поиска вариантов отелей в выбранном городе для команд /lowprice и /highprice
    """
    sort_order = None
    cur_user = User.get_user(user_id=user_id)
    command = cur_user.command
    city_id = cur_user.city_id
    check_in = cur_user.check_in
    check_out = cur_user.check_out
    hotels_count = cur_user.hotel_count
    if command == '/lowprice':
        sort_order = 'PRICE'
    elif command == '/highprice':
        sort_order = 'PRICE_HIGHEST_FIRST'
    result = hotel_info(destination_id=city_id, page_number='1', check_in=check_in, hotel_count=hotels_count,
                        check_out=check_out, price_min=None, price_max=None, sort_order=sort_order)
    if result is None:
        return None
    return result


def hotel_information(user_id: int):
    """
    Функция, которая собирает информацию об отелях для команд /lowprice и /highprice
    """
    cur_user = User.get_user(user_id=user_id)
    check_in = cur_user.check_in
    check_out = cur_user.check_out
    command = cur_user.command
    photo_count = cur_user.photo_count
    checks_in = str(check_in).split('-')
    checks_out = str(check_out).split('-')
    nights_count = int(checks_out[2]) - int(checks_in[2])
    hotels = lowprice_highprice_command(user_id=user_id)
    hotel_text = ''
    for index, hotel in enumerate(hotels, start=1):
        keyboard = hotel_keyboard(hotel)
        one_night_price = hotel['hotel_price']
        total = round(int(one_night_price) * nights_count, 3)
        hotels_info = f""" {index}) {hotel['hotel_name']}\n
        Рейтинг: {hotel['hotel_rating']} \u2B50\n
        Адрес: {hotel['hotel_country']}, {hotel['hotel_locality']}, {hotel['hotel_address']}\n
        Расстояние до центра: {hotel['hotel_distance_center']}\n
        Цена за одну ночь: ${one_night_price}\n
        Цена за весь период: ${total}\n"""
        hotel_text += hotels_info + '\n'
        if photo_count != 0:
            photos = photo_information(user_id=user_id, hotel=hotel)
            yield hotel['hotel_name'], keyboard, hotels_info, photos
        else:
            yield hotel['hotel_name'], keyboard, hotels_info
    History.create(user_id=user_id, command=command, date_time=datetime.now(), hotels_info=hotel_text)


def photo_information(user_id: int, hotel: dict) -> list:
    """
    Функция собирает для пользователя нужное количество фотографий
    """
    cur_user = User.get_user(user_id=user_id)
    photo_count = cur_user.photo_count
    photos = []
    if photo_count != 0:
        result = photo_info(hotel_id=hotel['hotel_id'], photo_amount=photo_count)
        for index_photo in result:
            result = InputMediaPhoto(index_photo)
            photos.append(result)
            return photos


def bestdeal_hotel_information(user_id: int):
    """
    Функция собирает информацию об отелях для команды /bestdeal
    """
    cur_user = User.get_user(user_id=user_id)
    check_in = cur_user.check_in
    check_out = cur_user.check_out
    hotels_amount = int(cur_user.hotel_count)
    photo_count = cur_user.photo_count
    distance_min = cur_user.distance_min
    distance_max = cur_user.distance_max
    page_number = 1
    hotels_count = 0
    while hotels_count == 0 and int(hotels_amount) > 0:
        hotels_count = 25
        result = bestdeal_command(user_id=user_id)
        checks_in = str(check_in).split('-')
        checks_out = str(check_out).split('-')
        nights_count = int(checks_out[2]) - int(checks_in[2])
        hotel_text = ''
        for index, hotel in enumerate(result, start=1):
            hotels_count -= 1
            keyboard = hotel_keyboard(hotel)
            distance = float(hotel['hotel_distance_center'].split()[0].split(',')[0])
            if not int(distance_min) < distance < int(distance_max):
                one_night_price = hotel['hotel_price']
                total = round(int(one_night_price) * nights_count, 3)
                hotels_info = f""" {index}) {hotel['hotel_name']}\n
                Рейтинг: {hotel['hotel_rating']} \u2B50\n
                Адрес: {hotel['hotel_country']}, {hotel['hotel_locality']}, {hotel['hotel_address']}\n
                Расстояние до центра: {hotel['hotel_distance_center']}\n
                Цена за одну ночь: ${one_night_price}\n
                Цена за весь период: ${total}\n"""
                hotel_text += hotels_info + '\n'
                if photo_count != 0:
                    photos = photo_information(user_id=user_id, hotel=hotel)
                    yield hotel['hotel_name'], keyboard, hotels_info, photos
                else:
                    yield hotel['hotel_name'], keyboard, hotels_info
                hotels_amount -= 1
            page_number += 1
        History.create(user_id=user_id, command='/bestdeal', date_time=datetime.now(), hotels_info=hotel_text)


def bestdeal_command(user_id: int) -> dict or None:
    """
    Функция для поиска отелей в выбранном городе для команды /bestdeal
    """
    cur_user = User.get_user(user_id=user_id)
    price_min = cur_user.price_min
    price_max = cur_user.price_max
    city_id = cur_user.city_id
    check_in = cur_user.check_in
    check_out = cur_user.check_out
    hotels_amount = int(cur_user.hotel_count)
    page_number = 1
    result = hotel_info(destination_id=city_id, page_number=str(page_number), check_in=check_in,
                        hotel_count=str(hotels_amount),
                        check_out=check_out, price_min=price_min, price_max=price_max,
                        sort_order='DISTANCE_FROM_LANDMARK')
    if result is None:
        return None
    return result
