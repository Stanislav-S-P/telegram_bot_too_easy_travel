from telebot.types import CallbackQuery
from database.models import user
from loader import bot, logger, exception_handler
from telegram_bot_calendar import DetailedTelegramCalendar
from keyboards.keyboards_text import LSTEP
from settings import constants
from datetime import date, timedelta, datetime
from handlers import lowprice_highprice


class CustomCalendar(DetailedTelegramCalendar):
    """
    Дочерний Класс (Родитель - DetailedTelegramCalendar). Необходим для изменения
    дефолтного значения у параметров empty month_button и empty_year_button.
    """
    empty_month_button: str = ''
    empty_year_button: str = ''


@exception_handler
def date_in(call: CallbackQuery) -> None:
    """
    Функция - запрашивающая у пользователя минимальную дату для проживания в отеле.
    После запроса, для взаимодействия с пользователем, создаёт inline-календарь.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    calendar, step = CustomCalendar(
        calendar_id=0,
        locale='ru',
        min_date=date.today() + timedelta(days=1),
        max_date=date.today() + timedelta(days=180)
    ).build()
    bot.send_message(call.from_user.id, constants.DATE_IN)
    bot_message = bot.send_message(call.from_user.id, f"Выберите {LSTEP[step]}:", reply_markup=calendar)
    user.edit('bot_message', bot_message)


@exception_handler
@bot.callback_query_handler(func=CustomCalendar.func(calendar_id=0))
def callback_first_calendar(call: CallbackQuery) -> None:
    """
    Функция - обработчик inline-календаря. Реагирует только на календарь с id = 0.
    После обработки пользовательской информации, перенаправляет в функцию date_out.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    result, key, step = CustomCalendar(
        calendar_id=0,
        locale='ru',
        min_date=date.today(),
        max_date=date.today() + timedelta(days=180)
    ).process(call.data)
    if not result and key:
        bot_message = bot.edit_message_text(
            f"Выберите {LSTEP[step]}:", call.message.chat.id, call.message.message_id, reply_markup=key
        )
        user.edit('bot_message', bot_message)
    elif result:
        bot.edit_message_text(f"Дата заезда {result}", call.message.chat.id, call.message.message_id)
        user.edit('date_in', result)
        date_out(call, result)


@exception_handler
def date_out(call: CallbackQuery, result: datetime) -> None:
    """
    Функция - запрашивающая у пользователя максимальную дату для проживания в отеле.
    После запроса,для взаимодействия с пользователем, создаёт inline-календарь.

    :param call: CallbackQuery
    :param result: datetime
    :return: None
    """
    logger.info(str(call.from_user.id))
    min_date = result + timedelta(days=1)
    second_calendar, second_step = CustomCalendar(
        calendar_id=15,
        locale='ru',
        min_date=min_date,
        max_date=min_date + timedelta(days=180)
    ).build()
    bot.send_message(call.from_user.id, constants.DATE_OUT)
    bot_message = bot.send_message(
        call.from_user.id, f"Выберите {LSTEP[second_step]}:", reply_markup=second_calendar
    )
    user.edit('bot_message', bot_message)


@exception_handler
@bot.callback_query_handler(func=CustomCalendar.func(calendar_id=15))
def callback_second_calendar(call: CallbackQuery) -> None:
    """
    Функция - обработчик inline-календаря. Реагирует только на календарь с id = 15.
    После обработки пользовательской информации, перенаправляет в функцию choice_photo,
    файла lowprice_highprice.

    :param call: CallbackQuery
    :return: None
    """
    logger.info(str(call.from_user.id))
    min_date = user.user.date_in + timedelta(days=1)
    result, key, step = CustomCalendar(
        calendar_id=15,
        locale='ru',
        min_date=min_date,
        max_date=min_date + timedelta(days=180)
    ).process(call.data)
    if not result and key:
        bot_message = bot.edit_message_text(
            f"Выберите {LSTEP[step]}:", call.message.chat.id, call.message.message_id, reply_markup=key
        )
        user.edit('bot_message', bot_message)
    elif result:
        bot.edit_message_text(f"Дата выезда {result}", call.message.chat.id, call.message.message_id)
        day_period = int(str(result - user.user.date_in).split()[0])
        user.edit('day_period', day_period)
        user.edit('date_in', datetime.strftime(user.user.date_in, '%Y-%m-%d'))
        user.edit('date_out', datetime.strftime(result, '%Y-%m-%d'))
        lowprice_highprice.choice_photo(call)
