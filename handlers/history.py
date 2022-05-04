import string
import requests

from typing import Union, List
from telebot.types import Message, InputMediaPhoto, CallbackQuery
from database.models import DataBaseModel, user
from keyboards.keyboards import keyboard_commands
from loader import bot, exception_handler
from settings import constants
from keyboards import keyboards, keyboards_text
from main import logger


def history_menu(message: Union[Message, CallbackQuery]) -> None:
    """
    Функция выводит пользователю меню раздела History в виделе inline-кнопок.
    Проверяет входящий аргумент на тип данных.

    :param message: Message
    :return: None
    """
    logger.info(str(message.from_user.id))
    if isinstance(message, Message):
        message_text = message.text
    else:
        message_text = message.data
    bot_message = bot.send_message(
        message.from_user.id, constants.HISTORY_MENU_MESSAGE, reply_markup=keyboards.keyboard_history(message_text)
    )
    user.edit('bot_message', bot_message)


@bot.callback_query_handler(func=lambda call: call.data in keyboards_text.HISTORY_LIST)
def callback_history_menu(call: CallbackQuery) -> None:
    """
    Функция - обработчик  inline-кнопок. Реагирует только на элменты списка HISTORY_LIST.
    В случае выбора пользователем - Просмотреть, выводит клавиатуру с подменю выбора режима просмотра истории.
    В случае выбора пользователем - Очистить, очищает историю пользователя и выводит сообщении
    об успешной очистке и дальнейших действиях.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    if call.data == keyboards_text.HISTORY_LIST[0]:
        bot_message = bot.send_message(
            call.from_user.id, constants.HISTORY_SHOW_MESSAGE, reply_markup=keyboards.keyboard_history(call.data)
        )
        user.edit('bot_message', bot_message)
    else:
        DataBaseModel.delete_history(call.from_user.id)
        bot.send_message(call.from_user.id, constants.HISTORY_DELETE)
        bot_message = bot.send_message(
            call.from_user.id, constants.HELP_MESSAGE, reply_markup=keyboard_commands(call.data)
        )
        user.edit('bot_message', bot_message)


@bot.callback_query_handler(func=lambda call: call.data in keyboards_text.HISTORY_SHOW_LIST)
@exception_handler
def callback_history_showing(call: CallbackQuery) -> None:
    """
    Функция - обработчик inline-кнопок. Реагирует только на команды из списка HISTORY_SHOW_LIST.
    Исходя из выбранного варианта, делает запрос к БД, и с полученным ответом перенаправляет в функцию
    history_showing. Если ответ пуст, то сообщает пользователю, что история пуста.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    if call.data == keyboards_text.HISTORY_SHOW_LIST[0]:
        user_command = DataBaseModel.select_history_user(call.from_user.id)
        if user_command:
            history_showing(call, user_command)
        else:
            bot.send_message(call.from_user.id, constants.HISTORY_EMPTY)
            bot_message = bot.send_message(
                call.from_user.id, constants.HELP_MESSAGE, reply_markup=keyboard_commands(call.data)
            )
            user.edit('bot_message', bot_message)
    else:
        user_command = DataBaseModel.select_history_user_five(call.from_user.id)
        if user_command:
            if len(user_command) > 5:
                user_command = user_command[:5]
            user_command.reverse()
            history_showing(call, user_command)
        else:
            bot.send_message(call.from_user.id, constants.HISTORY_EMPTY)
            bot_message = bot.send_message(
                call.from_user.id, constants.HELP_MESSAGE, reply_markup=keyboard_commands(call.data)
            )
            user.edit('bot_message', bot_message)


@exception_handler
def history_showing(call: CallbackQuery, user_command: List[tuple]) -> None:
    """
    Функция - обрабатывает ответ с БД и циклом выводит пользователю шаблон с данными о команде.
    Сам шаблон в зависимости от языка запроса получаем из функции locale_history.
    На каждой итерации делает запрос к БД, для получения истории найденных отелей. Если отели найдены,
    то направляется в функцию history_hotels_show. В противном случае, сообщает пользователю,
    что по данной команде не были найдены отели.

    :param call: CallbackQuery
    :param user_command: List[tuple]
    :return: None
    """
    logger.info(str(call.from_user.id))
    for command in user_command:
        history_template = locale_history(call, command[3])
        bot.send_message(call.from_user.id, history_template.format(
            command[1], command[2], command[3], command[4], command[5])
                         )
        hotels = DataBaseModel.select_history_hotel(command[0])
        if hotels:
            for hotel in hotels:
                history_hotels_show(call, hotel)
        else:
            bot.send_message(call.from_user.id, constants.HISTORY_EMPTY_HOTELS)
    bot.send_message(call.from_user.id, constants.HISTORY_COMPLETE)
    bot_message = bot.send_message(
        call.from_user.id, constants.HELP_MESSAGE, reply_markup=keyboard_commands(call.data)
    )
    user.edit('bot_message', bot_message)


@exception_handler
def history_hotels_show(call: CallbackQuery, hotel: tuple) -> None:
    """
    Функция - обрабатывающая кортеж с данными об отеле и выводящий пользователя информацию о найденном отеле.
    Если в БД хранились url фото, то выводит сообщение пользователю медиагруппой, с фотографиями.

    :param call: CallbackQuery
    :param hotel: tuple
    :return: None
    """
    logger.info(str(call.from_user.id))
    if hotel[1] != '':
        photo_list = hotel[1].split()
        media_massive = []
        index = 0
        for photo in photo_list:
            response = requests.get(photo)
            if str(response.status_code).startswith('2'):
                index += 1
                media_massive.append(
                    InputMediaPhoto(photo, caption=hotel[0] if index == 1 else '', parse_mode='Markdown')
                )
            else:
                logger.error('Ошибка запроса', exc_info=response.status_code)
        bot.send_media_group(call.from_user.id, media=media_massive)
    else:
        bot.send_message(call.from_user.id, hotel[0])


def locale_history(call: CallbackQuery, city: str) -> str:
    """
    Функция - проверяюща введённые пользователем данные и исходя из них,
    возвращает шаблон на русском, или английском языках.

    :param call: CallbackQuery
    :param city: str
    :return: str
    """
    logger.info(str(call.from_user.id))
    for sym in city:
        if sym not in string.printable:
            return constants.HISTORY_COMMAND_RU
    return constants.HISTORY_COMMAND_EN
