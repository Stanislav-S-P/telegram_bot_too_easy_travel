"""
Файл содержащий базовые конфигурации бота и API (Токен, API-ключ, заголовок, параметры и url-адреса)
"""

import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit('Файл .env отсутствует')
else:
    load_dotenv()

TOKEN = os.environ.get('TOKEN')
API_KEY = os.environ.get('API_KEY')


HEADERS = {
    'X-RapidAPI-Host': 'hotels4.p.rapidapi.com',
    'X-RapidAPI-Key': API_KEY
}


URL_SEARCH = 'https://hotels4.p.rapidapi.com/locations/v2/search'
URL_PROPERTY_LIST = 'https://hotels4.p.rapidapi.com/properties/list'
URL_PHOTO = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
URL_HOTEL = 'https://www.hotels.com/ho{}'


QUERY_SEARCH = {
    'query': 'new_york',
    'locale': 'en_US',
    'currency': 'USD'
}
QUERY_PROPERTY_LIST = {
    'destinationId': '1506246',
    'pageNumber': '1',
    'pageSize': '25',
    'checkIn': '2020-01-08',
    'checkOut': '2020-01-15',
    'adults1': '1',
    'sortOrder': 'PRICE',
    'locale': 'en_US',
    'currency': 'USD'
}
QUERY_BESTDEAL = {
    'destinationId': '1506246',
    'pageNumber': '1',
    'pageSize': '25',
    'checkIn': '2020-01-08',
    'checkOut': '2020-01-15',
    'adults1': '1',
    'priceMin': '50',
    'priceMax': '300',
    'sortOrder': 'DISTANCE_FROM_LANDMARK',
    'locale': 'en_US',
    'currency': 'EUR'
}
QUERY_PHOTO = {'id': '1178275040'}
