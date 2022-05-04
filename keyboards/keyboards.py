from typing import List
from telebot.types import InlineKeyboardMarkup
from keyboards import keyboards_text
from settings import constants
from telebot import types


def keyboard_commands(command: str) -> InlineKeyboardMarkup:
    """
    Функция - создаёт inline-клавиатуру для команд.

    :param command: str
    :return: InlineKeyboardMarkup
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    if command == constants.START:
        key_help = types.InlineKeyboardButton(text=keyboards_text.KEY_HELP, callback_data=constants.HELP)
        keyboard.add(key_help)
    elif command == constants.HELP:
        key_lowprice = types.InlineKeyboardButton(text=keyboards_text.KEY_LOWPRICE, callback_data=constants.LOWPRICE)
        key_highprice = types.InlineKeyboardButton(text=keyboards_text.KEY_HIGHPRICE, callback_data=constants.HIGHPRICE)
        key_bestdeal = types.InlineKeyboardButton(text=keyboards_text.KEY_BESTDEAL, callback_data=constants.BESTDEAL)
        key_history = types.InlineKeyboardButton(text=keyboards_text.KEY_HISTORY, callback_data=constants.HISTORY)
        keyboard.add(key_lowprice, key_highprice, key_bestdeal, key_history)
    return keyboard


def keyboards_currency() -> InlineKeyboardMarkup:
    """
    Функция - создаёт inline-клавиатуру со значениями валют.

    :return: InlineKeyboardMarkup
    """
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    key_list = []
    for currency in keyboards_text.CURRENCY_LIST:
        key = types.InlineKeyboardButton(text=currency, callback_data=currency)
        key_list.append(key)
    keyboard.add(key_list[0], key_list[1], key_list[2])
    return keyboard


def keyboards_city(city_list: List[tuple]) -> InlineKeyboardMarkup:
    """
    Функция - создаёт inline-клавиатуру с уточнением города поиска.

    :return: InlineKeyboardMarkup
    """
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for city in city_list:
        key = types.InlineKeyboardButton(text=city[1], callback_data=city[0])
        keyboard.add(key)
    return keyboard


def keyboards_photo() -> InlineKeyboardMarkup:
    """
    Функция - создаёт inline-клавиатуру с уточнением вывода фото.

    :return: InlineKeyboardMarkup
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    yes = types.InlineKeyboardButton(text=keyboards_text.CHOICE_PHOTO[0], callback_data=keyboards_text.CHOICE_PHOTO[0])
    no = types.InlineKeyboardButton(text=keyboards_text.CHOICE_PHOTO[1], callback_data=keyboards_text.CHOICE_PHOTO[1])
    keyboard.add(yes, no)
    return keyboard


def keyboards_count_photo() -> InlineKeyboardMarkup:
    """
    Функция - создаёт inline-клавиатуру с цифрами на кнопках от 1 до 10.
    Предназначена для запроса информации по количеству: отелей и фотографий

    :return: InlineKeyboardMarkup
    """
    keyboard = types.InlineKeyboardMarkup(row_width=5)
    key_list = []
    for num in keyboards_text.COUNT_PHOTO:
        key = types.InlineKeyboardButton(text=num[0], callback_data=num[1])
        key_list.append(key)
    keyboard.add(key_list[0], key_list[1], key_list[2], key_list[3], key_list[4],
                 key_list[5], key_list[6], key_list[7], key_list[8], key_list[9], )
    return keyboard


def keyboard_history(message: str) -> InlineKeyboardMarkup:
    """
    Функция - создаёт inline-клавиатуру с меню раздела History.

    :return: InlineKeyboardMarkup
    """
    keyboard = types.InlineKeyboardMarkup()
    if message == constants.HISTORY:
        keyboard_list = keyboards_text.HISTORY_LIST
    else:
        keyboard_list = keyboards_text.HISTORY_SHOW_LIST
    for elem in keyboard_list:
        key = types.InlineKeyboardButton(text=elem, callback_data=elem)
        keyboard.add(key)
    return keyboard
