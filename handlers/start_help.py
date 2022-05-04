from telebot.apihelper import ApiTelegramException
from telebot.types import Message, CallbackQuery
from database.models import user
from loader import bot, logger
from handlers import lowprice_highprice, history
from settings import constants
from keyboards.keyboards import keyboard_commands


@bot.message_handler(commands=constants.COMMAND)
def start_command(message: Message) -> None:
    """
    Функция - обработчик сообщений. Реагирует на команды из списка 'COMMAND'.
    Исходя из пойманной команды, отправляет пользователя в соответствующий сценарий.
    Первым делом, очищает экземпляр класса UserHandle,
    так как с данного места берут начало новые команды.

    :param message: Message
    :return: None
    """
    logger.info(str(message.from_user.id))
    check_state_inline_keyboard(user.user.bot_message)
    user.set_default()
    user.edit('user_id', message.from_user.id)
    if message.text == constants.START:
        bot.send_message(message.from_user.id, constants.WELCOME.format(message.from_user.first_name))
        bot_message = bot.send_message(
            message.from_user.id, constants.INSTRUCTION, reply_markup=keyboard_commands(message.text)
        )
        user.edit('bot_message', bot_message)
    elif message.text == constants.HELP:
        bot_message = bot.send_message(
            message.from_user.id, constants.HELP_MESSAGE, reply_markup=keyboard_commands(message.text)
        )
        user.edit('bot_message', bot_message)
    elif message.text in [constants.LOWPRICE, constants.HIGHPRICE, constants.BESTDEAL]:
        lowprice_highprice.record_command(message)
    elif message.text == constants.HISTORY:
        history.history_menu(message)


def suggest_finding_a_hotel(message: Message) -> None:
    """
    Функция - После ответа пользователя предлагает поискать отели

    :param message: Message
    :return: None
    """
    bot.send_message(message.from_user.id, constants.SUGGEST_FINDING)
    bot_message = bot.send_message(
        message.from_user.id, constants.HELP_MESSAGE, reply_markup=keyboard_commands(message.text)
    )
    user.edit('bot_message', bot_message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('/'))
def callback_command(call: CallbackQuery) -> None:
    """
    Функция - обработчик inline-кнопок. Реагирует только на команды.
    Исходя из пойманной команды, отправляет пользователя в соответствующий сценарий.
    Первым делом, очищает экземпляр класса UserHandle,
    так как с данного места берут начало новые команды.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    user.set_default()
    user.edit('user_id', call.from_user.id)
    if call.data == constants.HELP:
        bot_message = bot.send_message(
            call.from_user.id, constants.HELP_MESSAGE, reply_markup=keyboard_commands(call.data)
        )
        user.edit('bot_message', bot_message)
    elif call.data in [constants.LOWPRICE, constants.HIGHPRICE, constants.BESTDEAL]:
        lowprice_highprice.record_command(call)
    elif call.data == constants.HISTORY:
        history.history_menu(call)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


@bot.message_handler(state=None)
def echo_handler(message: Message) -> None:
    """
    Функция - обработчик всех входящих сообщений, не входящих в сценарий работы бота.
    Так же обрабатывает приветствия пользователя.

    :param message: Message
    :return: None
    """
    logger.info(str(message.from_user.id))
    message_text = message.text.lower()
    if message_text.startswith(constants.WELCOME_LIST[0]) or message_text.startswith(constants.WELCOME_LIST[1]):
        bot.send_message(message.from_user.id, constants.WELCOME.format(message.from_user.first_name))
        bot_message = bot.send_message(message.from_user.id, constants.INSTRUCTION)
        user.edit('bot_message', bot_message)
    elif message_text.startswith(constants.WELCOME_LIST[2]) or message_text.startswith(constants.WELCOME_LIST[3]):
        bot.send_message(message.from_user.id, constants.HOW_ARE_YOU_ANSWER)
        bot.register_next_step_handler(message, suggest_finding_a_hotel)
    elif message_text.startswith(constants.WELCOME_LIST[4]) or message_text.startswith(constants.WELCOME_LIST[5]):
        bot.send_message(message.from_user.id, constants.GOODBYE_MESSAGE)
        bot_message = bot.send_message(message.from_user.id, constants.INSTRUCTION)
        user.edit('bot_message', bot_message)
    else:
        bot.send_message(message.from_user.id, constants.WARNING_MESSAGE)


def check_state_inline_keyboard(message: Message) -> None:
    """
    Функция -  предназначена для удаления inline-кнопок, в случае не активного статуса
    (пользователь перешёл в другую команду). Чтобы исключить повторное нажатие на кнопку вне сценария,
    данная функция удаляет оставшиеся inline-кнопки, если кнопки нет, то возникает исключение
    ApiTelegramException, которое функция подавляет.

    :param message: Message
    :return: None
    """
    try:
        bot.edit_message_reply_markup(message.chat.id, message.message_id)
    except ApiTelegramException:
        pass
    except AttributeError:
        pass
