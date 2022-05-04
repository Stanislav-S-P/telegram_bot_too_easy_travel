import sqlite3

from dataclasses import dataclass
from typing import Union, List
from telebot.types import Message, CallbackQuery


@dataclass
class User:
    """
    Dataclass -  для хранения пользовательской информации
    """
    date: str = ''
    user_id: int = 0
    command: str = ''
    currency: str = ''
    locale: str = ''
    city: str = ''
    city_id: str = ''
    count_hotel: int = 0
    date_in: str = ''
    date_out: str = ''
    day_period: int = 0
    photo: str = ''
    count_photo: int = 0
    min_distance: float = 0
    max_distance: float = 0
    price_min: int = 0
    price_max: int = 0
    bot_message: Union[Message, CallbackQuery] = ''


class UserHandle:
    """
    Класс - для получения, заполнения и редактирования пользовательской информации
    """
    def __init__(self) -> None:
        self.user: User = User()

    def get_tuple(self) -> tuple:
        """
        Метод класса UserHandle (геттер), возвращающий кортеж значений, необходимых для записи в БД
        :return: tuple
        """
        return (
            self.user.date,
            self.user.user_id,
            self.user.command,
            self.user.city,
            self.user.currency,
            self.user.date_in,
            self.user.date_out,
            self.user.min_distance,
            self.user.max_distance,
            self.user.price_min,
            self.user.price_max
        )

    def set_default(self) -> None:
        """
        Метод класса UserHandle (сеттер), для присваивания атрибутам дефолтного значения
        :return: None
        """
        self.user.date = ''
        self.user.user_id = 0
        self.user.command = ''
        self.user.currency = ''
        self.user.locale = ''
        self.user.city = ''
        self.user.city_id = ''
        self.user.count_hotel = 0
        self.user.date_in = ''
        self.user.date_out = ''
        self.user.day_period = 0
        self.user.photo = ''
        self.user.count_photo = 0
        self.user.min_distance = 0
        self.user.max_distance = 0
        self.user.price_min = 0
        self.user.price_max = 0

    def edit(self, key: str, value: Union[str, int, float]) -> None:
        """
        Метод класса UserHandle (сеттер), для изменения данных по ключу
        :param key: str
        :param value: Union[str, int, float]
        :return: None
        """
        self.user.__dict__[key] = value


user = UserHandle()


class Hotel:
    """
    Класс для хранения информации об выведенных пользователю отелях
    """
    def __init__(self, user_id: int, hotel_info: str) -> None:
        self.user_id = user_id
        self.hotel_info = hotel_info
        self.photo = ''
        self.command_id = 0

    def get_tuple(self) -> tuple:
        """
        Метод класса Hotel (геттер), возвращающий кортеж значений, необходимых для записи в БД

        :return: tuple
        """
        return (
            self.user_id,
            self.hotel_info,
            self.photo,
            self.command_id,
        )


class DataBaseModel:
    """
    Класс, содержащий в себе методы запросов к БД
    """

    @classmethod
    def _init_user_tables(cls) -> None:
        """
        Класс-метод создающий базу данных и таблицу пользователя, в случае её отсутствия

        :return: None
        """
        with sqlite3.connect('hotel_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM 'sqlite_master' "
                "WHERE type='table' AND name='table_user';"
            )
            exists = cursor.fetchone()
            if not exists:
                cursor.executescript(
                    "CREATE TABLE 'table_user' ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "command_time TEXT NOT NULL,"
                    "user_id INTEGER NOT NULL, "
                    "command TEXT NOT NULL,"
                    "city TEXT NOT NULL,"
                    "currency TEXT NOT NULL,"
                    "date_in TEXT NOT NULL,"
                    "date_out TEXT NOT NULL,"
                    "min_distance REAL NOT NULL,"
                    "max_distance REAL NOT NULL,"
                    "price_min INTEGER NOT NULL,"
                    "price_max INTEGER NOT NULL)"
                )
        cls._init_hotel_tables()

    @classmethod
    def _init_hotel_tables(cls) -> None:
        """
        Класс-метод создающий базу данных и таблицу отелей, в случае её отсутствия

        :return: None
        """
        with sqlite3.connect('hotel_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM 'sqlite_master' "
                "WHERE type='table' AND name='table_hotel';"
            )
            exists = cursor.fetchone()
            if not exists:
                cursor.executescript(
                    "CREATE TABLE 'table_hotel' ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "user_id INTEGER NOT NULL, "
                    "hotel_info TEXT NOT NULL,"
                    "photo TEXT NOT NULL,"
                    "command_id INTEGER NOT NULL,"
                    "FOREIGN KEY (command_id) REFERENCES table_user(id) ON DELETE CASCADE)"
                )
            cursor.executescript("PRAGMA foreign_keys = ON;")

    @classmethod
    def insert_user(cls, user_tuple: tuple) -> None:
        """
        Класс-метод записывающий данные пользователя в БД

        :param user_tuple: tuple
        :return: None
        """
        with sqlite3.connect('hotel_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO 'table_user' ("
                "command_time, user_id, command, city, currency, date_in, "
                "date_out, min_distance, max_distance, price_min, price_max) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", user_tuple
            )

    @classmethod
    def insert_hotel(cls, user_hotel: Hotel) -> None:
        """
        Класс-метод записывающий данные отеля в БД

        :param user_hotel: Hotel
        :return: None
        """
        with sqlite3.connect('hotel_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM 'table_user' "
                           "WHERE user_id = {} ORDER BY id DESC ".format(user.user.user_id))
            command_id, *_ = cursor.fetchone()
            user_hotel.command_id = command_id
            cursor.execute(
                "INSERT INTO 'table_hotel' ("
                "user_id, hotel_info, photo, command_id) "
                "VALUES (?, ?, ?, ?)", user_hotel.get_tuple()
            )

    @classmethod
    def delete_history(cls, history_user: int) -> None:
        """
        Класс-метод удаляющий из базы данных записи текущего пользователя

        :param history_user: int
        :return: None
        """
        with sqlite3.connect('hotel_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM 'table_user' WHERE user_id = ?;", (history_user, )
            )
            cursor.execute(
                "DELETE FROM 'table_hotel' WHERE user_id = ?;", (history_user,)
            )

    @classmethod
    def select_history_user(cls, history_user: int) -> List[tuple]:
        """
        Класс-метод возвращающий из базы данных список кортежей с информацией по пользователю.

        :param history_user: int
        :return: List[tuple]
        """
        with sqlite3.connect('hotel_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, command_time, command, city, date_in, date_out "
                "FROM 'table_user' WHERE user_id = ?", (history_user, )
            )
            user_command = cursor.fetchall()
            return user_command

    @classmethod
    def select_history_user_five(cls, history_user: int) -> List[tuple]:
        """
        Класс-метод возвращающий из базы данных список кортежей с информацией по пользователю,
        отсортированной в обратном порядке для вывода последних пяти записей.

        :param history_user: int
        :return: List[tuple]
        """
        with sqlite3.connect('hotel_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, command_time, command, city, date_in, date_out "
                "FROM 'table_user' WHERE user_id = ? ORDER BY id DESC ", (history_user, )
            )
            user_command = cursor.fetchall()
            return user_command

    @classmethod
    def select_history_hotel(cls, history_id: int) -> List[tuple]:
        """
        Класс-метод возвращающий из базы данных список кортежей с информацией по отелям,
        запрошенным ранее пользователем

        :param history_id: int
        :return: List[tuple]
        """
        with sqlite3.connect('hotel_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT hotel_info, photo "
                "FROM 'table_hotel' WHERE command_id = ?", (history_id, ))
            user_hotels = cursor.fetchall()
            return user_hotels
