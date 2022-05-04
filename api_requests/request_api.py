import requests
import string

from requests import Response
from telebot.types import Message, CallbackQuery
from database.models import user
from loader import logger, exception_request_handler
from settings import constants
from settings.settings import QUERY_SEARCH, URL_SEARCH, HEADERS, QUERY_PROPERTY_LIST, URL_PROPERTY_LIST, QUERY_PHOTO, \
    URL_PHOTO, QUERY_BESTDEAL


@exception_request_handler
def request_search(message: Message) -> Response:
    """
    Функция - делающая запрос на API по адресу: 'https://hotels4.p.rapidapi.com/locations/v2/search'
    Проверяет введённые пользователем символы на ASCII кодировку, если так, то ищет с параметром locale en_US,
    в противном случае ищет с парметром locale ru_RU. Возвращает Response, содержащий в себе список городов.

    :param message: Message
    :return: Response
    """
    logger.info(str(message.from_user.id))
    for sym in message.text:
        if sym not in string.printable:
            QUERY_SEARCH['locale'] = 'ru_RU'
            break
    QUERY_SEARCH['currency'] = user.user.currency
    QUERY_SEARCH['query'] = message.text
    user.edit('locale', QUERY_SEARCH['locale'])
    response = requests.request('GET', URL_SEARCH, headers=HEADERS, params=QUERY_SEARCH, timeout=15)
    return response


@exception_request_handler
def request_property_list(call: CallbackQuery) -> Response:
    """
    Функция - делающая запрос на API по адресу: 'https://hotels4.p.rapidapi.com/properties/list'
    Предназначена для команд lowprice и highprice. В зависимости от введенной команды сортирует ответ
    по возврастанию цены, или же по убыванию. Возвращает Response, содержащий в себе список отелей в выбранном городе.

    :param call: CallbackQuery
    :return: Response
    """
    logger.info(str(call.from_user.id))
    if user.user.command == constants.HIGHPRICE[1:]:
        QUERY_PROPERTY_LIST['sortOrder'] = '-PRICE'
    QUERY_PROPERTY_LIST['destinationId'] = user.user.city_id
    QUERY_PROPERTY_LIST['checkIn'] = user.user.date_in
    QUERY_PROPERTY_LIST['checkOut'] = user.user.date_out
    QUERY_PROPERTY_LIST['currency'] = user.user.currency
    QUERY_PROPERTY_LIST['locale'] = user.user.locale
    response = requests.request('GET', URL_PROPERTY_LIST, headers=HEADERS, params=QUERY_PROPERTY_LIST, timeout=15)
    return response


@exception_request_handler
def request_bestdeal(call: CallbackQuery) -> Response:
    """
    Функция - делающая запрос на API по адресу: 'https://hotels4.p.rapidapi.com/properties/list'. Предназначена для
    команды bestdeal. Исключительность данной функции под функционал одной команды заключается в широкой
    установке параметров для поиска. Возвращает Response, содержащий в себе список отелей в выбранном городе.

    :param call: CallbackQuery
    :return: Response
    """
    logger.info(str(call.from_user.id))
    QUERY_BESTDEAL['destinationId'] = user.user.city_id
    QUERY_BESTDEAL['checkIn'] = user.user.date_in
    QUERY_BESTDEAL['checkOut'] = user.user.date_out
    QUERY_BESTDEAL['priceMin'] = user.user.price_min
    QUERY_BESTDEAL['priceMax'] = user.user.price_max
    QUERY_BESTDEAL['currency'] = user.user.currency
    QUERY_BESTDEAL['locale'] = user.user.locale
    response = requests.request('GET', URL_PROPERTY_LIST, headers=HEADERS, params=QUERY_BESTDEAL, timeout=15)
    return response


@exception_request_handler
def request_get_photo(call: CallbackQuery, hotel_id: int) -> Response:
    """
    Функция - делающая запрос на API по адресу: 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'.
    Вызывается при необходимости вывода фотографий к отелям. Возвращает Response, содержащий в себе список url
    фотографий отелей.

    :param call: CallbackQuery
    :param hotel_id: int
    :return: Response
    """
    logger.info(str(call.from_user.id))
    QUERY_PHOTO['id'] = hotel_id
    response = requests.request('GET', URL_PHOTO, headers=HEADERS, params=QUERY_PHOTO, timeout=15)
    return response
