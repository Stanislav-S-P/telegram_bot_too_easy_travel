import json
import re
import requests

from typing import Union, Any, Dict, Optional, List, Tuple
from requests.models import Response
from datetime import datetime
from keyboards.keyboards import keyboard_commands
from loader import bot, logger, exception_handler
from database.models import user, DataBaseModel, Hotel
from settings import constants
from settings import settings
from . import bestdeal
from api_requests.request_api import request_search, request_property_list, request_get_photo, request_bestdeal
from keyboards import keyboards, keyboards_text, calendar
from telebot.types import CallbackQuery, InputMediaPhoto, Message
from .start_help import start_command, check_state_inline_keyboard


@exception_handler
def record_command(message: Union[Message, CallbackQuery]) -> None:
    """
    Функция, запускающая команды: 'lowprice', 'highprice', 'bestdeal'. Проверяет входящий тип
    данных из предыдущей функции. С данной функции осуществляется начало сбора информации
    по команде, для дальнейшего сохранения в базу данных. Так же функция оповещает пользователя,
    что поиск Российских городов временно приостановлен.

    :param message: Union[Message, CallbackQuery]
    :return: None
    """
    logger.info(str(message.from_user.id))
    check_state_inline_keyboard(message)
    if isinstance(message, CallbackQuery):
        user.edit('command', message.data[1:])
    else:
        user.edit('command', message.text[1:])
    bot.send_message(message.from_user.id, constants.DATA_ON_RUSSIAN_CITIES)
    choice_city(message)


@exception_handler
def choice_city(message: Union[Message, CallbackQuery]) -> None:
    """
    Функция, проверяет входящий тип данных из предыдущей функции и запрашивает город
    для поиска отелей.

    :param message: Union[Message, CallbackQuery]
    :return: None
    """
    logger.info(str(message.from_user.id))
    bot.send_message(message.from_user.id, constants.CITY)
    if isinstance(message, CallbackQuery):
        bot.register_next_step_handler(message.message, search_city)
    else:
        bot.register_next_step_handler(message, search_city)


@exception_handler
def search_city(message: Message) -> None:
    """
    Функция - обрабатывает введённый пользователем город. Делает запрос на rapidapi.com.
    В случае ошибки запроса, сообщает о неполадках и возвращает пользователя на ввод города.
    В случае положительного ответа, обрабатывает его и в виде inline-кнопок отправляет
    пользователю все похожие варианты ответа.

    :param message: Message
    :return: None
    """
    logger.info(str(message.from_user.id))
    if message.text in constants.COMMAND_LIST:
        start_command(message)
    else:
        response = request_search(message)
        if check_status_code(response):
            pattern_city_group = r'(?<="CITY_GROUP",).+?[\]]'
            find_cities = re.findall(pattern_city_group, response.text)
            if len(find_cities[0]) > 20:
                pattern_dest = r'(?<="destinationId":")\d+'
                destination = re.findall(pattern_dest, find_cities[0])
                pattern_city = r'(?<="name":")\w+[\s, \w]\w+'
                city = re.findall(pattern_city, find_cities[0])
                city_list = list(zip(destination, city))
                bot_message = bot.send_message(
                    message.from_user.id, constants.CORRECTION, reply_markup=keyboards.keyboards_city(city_list)
                )
                user.edit('bot_message', bot_message)
            else:
                bot.send_message(message.from_user.id, constants.INCORRECT_CITY)
                choice_city(message)
        else:
            bot.send_message(message.from_user.id, constants.REQUEST_ERROR)
            choice_city(message)


@bot.callback_query_handler(func=lambda call: call.data.isdigit())
@exception_handler
def callback_city(call: CallbackQuery) -> None:
    """
    Функция - обработчик inline-кнопок. Реагирует только на информацию из кнопок
    выбора города. Далее, в формате inline-кнопок, предоставляет пользователю выбор валюты.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    for city in call.message.json['reply_markup']['inline_keyboard']:
        if city[0]['callback_data'] == call.data:
            user.edit('city', city[0]['text'])
            user.edit('city_id', call.data)
            break
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.edit_message_text(
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=constants.CITY_RESULT.format(user.user.city)
    )
    bot_message = bot.send_message(
        call.from_user.id, constants.CURRENCY, reply_markup=keyboards.keyboards_currency()
    )
    user.edit('bot_message', bot_message)


@bot.callback_query_handler(func=lambda call: call.data in keyboards_text.CURRENCY_LIST)
@exception_handler
def callback_currency(call: CallbackQuery) -> None:
    """
    Функция - обработчик inline-кнопок. Реагирует только на информацию входящую
    в список аббревиатур валют. Если начальная команда введенная пользователем равна 'bestdeal',
    то запрашиваем у пользователя информацию о диапазоне цен. Переходя в файл 'bestdeal.py', функцию 'price_min'
    Если команда равна 'lowprice', или 'highprice', переходим в следующую функцию 'count_hotel'.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.edit_message_text(
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        text=constants.RESULT_CURRENCY.format(call.data)
    )
    user.edit('currency', call.data)
    if user.user.command != constants.BESTDEAL[1:]:
        count_hotel(call)
    else:
        bot.send_message(call.from_user.id, constants.PRICE_RANGE.format(user.user.currency))
        bot_message = bot.send_message(call.from_user.id, constants.MIN_PRICE)
        user.edit('bot_message', bot_message)
        bot.register_next_step_handler(call.message, bestdeal.price_min)


def count_hotel(call: CallbackQuery) -> None:
    """
    Функция - предоставляющая пользователю выбрать количество отелей (от 1 до 10), в формате inline-кнопок.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    bot_message = bot.send_message(
        call.from_user.id, constants.COUNT_HOTEL, reply_markup=keyboards.keyboards_count_photo()
    )
    user.edit('bot_message', bot_message)


def choice_photo(call: CallbackQuery):
    """
    Функция - уточняющая у пользователя необходимость вывода фотографий к отелям, в формате inline-кнопок.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    bot_message = bot.send_message(
        call.from_user.id, constants.QUESTION_PHOTO, reply_markup=keyboards.keyboards_photo()
    )
    user.edit('bot_message', bot_message)


@bot.callback_query_handler(func=lambda call: call.data in keyboards_text.CHOICE_PHOTO)
@exception_handler
def callback_photo(call: CallbackQuery) -> None:
    """
    Функция - обработчик inline-кнопок. Реагирует только на информацию входящую в список 'CHOICE_PHOTO'
    В случае положительного ответа, запрашивает информацию о количестве фотографий для вывода,
    в формате inline-кнопок. Если полученный ответ отрицательный, то отправляет далее по сценарию в функцию
    'load_result'.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    user.edit('photo', call.data)
    if call.data == 'Да':
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=constants.YES_QUESTION_PHOTO
        )
        bot_message = bot.send_message(
            call.from_user.id, constants.COUNT_PHOTO, reply_markup=keyboards.keyboards_count_photo()
        )
        user.edit('bot_message', bot_message)
    elif call.data == 'Нет':
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=constants.NO_QUESTION_PHOTO
        )
        load_result(call)


@bot.callback_query_handler(func=lambda call: call.data in keyboards_text.CALLBACK_PHOTO)
@exception_handler
def callback_count_photo(call: CallbackQuery) -> None:
    """
    Функция - обработчик inline-кнопок. Реагирует только на запросы о количестве отелей и количестве фотографий.
    Исходя из дефолтных данных у экземпляра класса UserHandle, направляет пользователя далее.
    Если аргумент 'count_hotel', имеет дефолтное значение (0), то переходим в функцию date_in, файла calendar,
    пакета keyboards. Если значение не равно нулю, то отправляет далее по сценарию в функцию
    'load_result'.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    for elem in call.message.json['reply_markup']['inline_keyboard']:
        for num in elem:
            if num['callback_data'] == call.data:
                if user.user.count_hotel == 0:
                    user.edit('count_hotel', int(num['text']))
                    bot.edit_message_text(
                        chat_id=call.message.chat.id, message_id=call.message.message_id,
                        text=constants.RESULT_COUNT_HOTEL.format(user.user.count_hotel)
                    )
                    calendar.date_in(call)
                else:
                    user.edit('count_photo', int(num['text']))
                    bot.edit_message_text(
                        chat_id=call.message.chat.id, message_id=call.message.message_id,
                        text=constants.RESULT_COUNT_PHOTO.format(user.user.count_photo)
                    )
                    load_result(call)


@exception_handler
def load_result(call: CallbackQuery) -> None:
    """
    Функция - записывающая последний аргумент в экземпляр класса UserHandle.
    Оповещает пользователя о выполнении загрузки. Проверяет, если пользователь выбирал команду 'bestdeal',
    то делает запрос к API (request_bestdeal), в противном случае делает запрос к API (request_property_list).
    Далее с ответом из API осуществляется переход в функцию 'request_hotels'.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    user.edit('date', datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'))
    bot.send_message(call.from_user.id, constants.LOAD_RESULT)
    if user.user.command == constants.BESTDEAL[1:]:
        response_hotels = request_bestdeal(call)
    else:
        response_hotels = request_property_list(call)
    request_hotels(call, response_hotels)


@exception_handler
def request_hotels(call: CallbackQuery, response_hotels: Response) -> None:
    """
    Функция - обрабатывающая ответ с API. Если статус код успешный, то создаётся запись в БД,
    о команде пользователя. Ответ с API десериализуется и проверяется в экземпляре пользователя введённая команда.
    Если команда 'bestdeal результат поиска дополнительно обрабатывается в функции 'bestdeal_logic' файла 'bestdeal'.
    И затем осуществляется переход в функцию showing_hotels. Если статус код ответа не успешный,
    то пользователю выдаётся сообщение об ошибке поиска.

    :param call: CallbackQuery
    :param response_hotels: Response
    :return: None
    """
    logger.info(str(call.from_user.id))
    if check_status_code(response_hotels):
        DataBaseModel.insert_user(user.get_tuple())
        result_hotels = json.loads(response_hotels.text)['data']['body']['searchResults']['results']
        if user.user.command == constants.BESTDEAL[1:]:
            result_hotels = bestdeal.bestdeal_logic(call, result_hotels, result=[])
            if result_hotels is False:
                bot.send_message(call.from_user.id, constants.NOT_FOUND)
                bot_message = bot.send_message(
                    call.from_user.id, constants.HELP_MESSAGE, reply_markup=keyboard_commands(constants.HELP)
                )
                user.edit('bot_message', bot_message)
            else:
                showing_hotels(call, result_hotels)
        else:
            showing_hotels(call, result_hotels)
    else:
        bot.send_message(call.from_user.id, constants.REQUEST_ERROR)
        bot_message = bot.send_message(
            call.from_user.id, constants.INSTRUCTION, reply_markup=keyboard_commands(call.data)
        )
        user.edit('bot_message', bot_message)


@exception_handler
def showing_hotels(call: CallbackQuery, result_hotels: Any) -> None:
    """
    Функция - выводит пользователю информацию по отелям. Подставляя данные по отелям в шаблон,
    в функции 'hotel_template'. Вывод осуществляется при условии, что пользователь отказался от вывода фото,
    в противном случае осуществляем переход в функцию 'showing_hotels_with_photo'.
    Так же, если вывод осущствлен, происходит запись данных об отеле в БД.

    :param call: CallbackQuery
    :param result_hotels: Any
    :return: None
    """
    logger.info(str(call.from_user.id))
    index = 0
    for hotel in result_hotels:
        if index == user.user.count_hotel:
            bot.send_message(call.from_user.id, constants.SEARCH_RESULT)
            bot_message = bot.send_message(
                call.from_user.id, constants.INSTRUCTION, reply_markup=keyboard_commands(call.data)
            )
            user.set_default()
            user.edit('bot_message', bot_message)
            break
        else:
            hotel_show = hotel_template(
                call=call, currency=user.user.currency, days=user.user.day_period, hotel=hotel
            )
            if hotel_show is not None:
                index += 1
                user_hotel = Hotel(call.from_user.id, hotel_show)
                if user.user.count_photo != 0:
                    showing_hotels_with_photo(call, hotel, hotel_show, user_hotel)
                else:
                    DataBaseModel.insert_hotel(user_hotel)
                    bot.send_message(call.from_user.id, hotel_show, parse_mode='Markdown')


def hotel_template(call: CallbackQuery, currency: str, days: int, hotel: Dict) -> Optional[str]:
    """
    Функция - подставляющая параметры отеля в шаблон. Для выбора русскоязычного шаблона,
    или англоязычного, делается запрос в функцию 'locale_choice', которая и возаращает нужный шаблон.

    :param call: CallbackQuery
    :param currency: str
    :param days: int
    :param hotel: Dict
    :return: Optional[str]
    """
    logger.info(str(call.from_user.id))
    try:
        hotel_show = locale_choice(call)
        link = settings.URL_HOTEL.format(hotel['id'])
        if currency == 'USD':
            price = int(hotel['ratePlan']['price']['current'][1:])
            cur_sym = '$'
            price_per_period = price * days
        elif currency == 'EUR':
            price = int(hotel['ratePlan']['price']['current'][:-2])
            cur_sym = '€'
            price_per_period = price * days
        else:
            price = hotel['ratePlan']['price']['current'][:-4]
            price_ru = re.sub(r'[,]', '', price)
            price_per_period = int(price_ru) * days
            cur_sym = 'RUB'
        name = hotel['name']
        address = hotel['address']['streetAddress']
        distance = hotel['landmarks'][0]['distance']
        star_rating = hotel['starRating']
        return hotel_show.format(
            name, address, distance, price,
            cur_sym, price_per_period,
            cur_sym, star_rating, link
        )
    except KeyError:
        return None


def locale_choice(call: CallbackQuery) -> str:
    """
    Функция - возвращающая необходимый шаблон в функцию 'hotel_template'.
    Проверка осуществляется по совпадению атрибута locale у экземпляра класса пользователя.

    :param call: CallbackQuery
    :return: str
    """
    logger.info(str(call.from_user.id))
    if user.user.locale == 'en_US':
        hotel_show = constants.HOTEL_SHOW_EN
    else:
        hotel_show = constants.HOTEL_SHOW_RU
    return hotel_show


@exception_handler
def showing_hotels_with_photo(call: CallbackQuery, hotel: Dict, hotel_show: str, user_hotel: Hotel) -> None:
    """
    Функция - вызываемая в случае, если пользователь указал наличие фотографий к отелям. Делается запрос к API.
    Если ответ с успешным статус-кодом, то дополнительно вызывается функция 'photo_append', из которой получаем список
    медиа-инпутов. Показ информации об отеле осуществляется медиа-группой. Так же в функции происходит
    сохранение инфо по отелю в БД.

    :param call: CallbackQuery
    :param hotel: Dict
    :param hotel_show: str
    :param user_hotel: Hotel
    :return: None
    """
    logger.info(str(call.from_user.id))
    response_photo = request_get_photo(call, hotel['id'])
    if check_status_code(response_photo):
        result_photo = json.loads(response_photo.text)['hotelImages']
        media_massive, photo_str = photo_append(call, result_photo, hotel_show)
        bot.send_media_group(call.from_user.id, media=media_massive)
        user_hotel.photo = photo_str
        DataBaseModel.insert_hotel(user_hotel)


@exception_handler
def photo_append(call: CallbackQuery, result_photo: List, hotel_show: str) -> Tuple[List, str]:
    """
    Функция подготавливающая список с медиа-инпутами для медиа-группы.
    Так же проверяет запросы к фотографиям на наличие ошибки.

    :param call: CallbackQuery
    :param result_photo: List
    :param hotel_show: str
    :return: tuple[List, str]
    """
    logger.info(str(call.from_user.id))
    index = 0
    photo_str = ''
    media_massive = []
    for photo_dict in result_photo:
        if index == user.user.count_photo:
            return media_massive, photo_str
        else:
            photo_str += photo_dict['baseUrl'].format(size='y') + ' '
            photo = photo_dict['baseUrl'].format(size='y')
            response = requests.get(photo)
            if check_status_code(response):
                index += 1
                media_massive.append(
                    InputMediaPhoto(photo, caption=hotel_show if index == 1 else '', parse_mode='Markdown')
                )


def check_status_code(response: Response) -> Optional[bool]:
    """
    Функция - проверяет статус-код ответа. Если статус-код начинается на '2', то возвращает True,
    в противном случае пишет лог об ошибке.

    :param response: Response
    :return: Optional[bool]
    """
    if str(response.status_code).startswith('2'):
        return True
    else:
        logger.error('Ошибка запроса', exc_info=response.status_code)
