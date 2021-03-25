import os

import telebot

from typing import List, Union
from datetime import datetime

from utils.database import HerokuDB

ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


def zlog(message):
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    bot.send_message(ADMIN_USER_ID, message)


class Chat:
    def __init__(self, **fields):
        self.last_message = fields.get("last_message", "")
        self.last_message_at = fields.get("last_message_at", "")

    def to_dict(self):
        return self.__dict__


class Reminder:
    def __init__(self, **fields):
        self.reminder_id = fields.get("reminder_id", "")
        self.title = fields.get("title", "")
        self.remind_at = fields.get("remind_at", "")
        self.created_at = fields.get("created_at", "")
        self.updated_at = fields.get("updated_at", "")

    def to_dict(self):
        return self.__dict__


class User:
    def __init__(self, **fields):
        self.nickname: str = fields.get("nickname", "")
        self.telegram_id: str = fields.get("telegram_id", "")
        if not str(self.telegram_id).isnumeric:
            raise Exception("User telegram_id must be the numeric id given by the Telegram user request.")
        self.chat: Chat = Chat(**fields.get("chat", {}))
        self.reminders: List[Reminder] = [Reminder(**reminder) for reminder in fields.get("reminders", [])]

    def get_reminders(self):
        self.db = HerokuDB()
        self.db.cursor.execute(f"SELECT * FROM reminders WHERE telegram_id = '{self.telegram_id}' ORDER BY remind_at")
        reminders = self.db.fetchall()
        columns = self.db.get_columns("reminders")
        data = [{columns[i][0]: reminder[i] for i in range(len(reminder))} for reminder in reminders]
        self.reminders = [Reminder(**reminder) for reminder in data]
        self.db.conn.close()

    def get_chat(self):
        self.db = HerokuDB()
        self.db.cursor.execute(f"SELECT * FROM chats WHERE telegram_id = '{self.telegram_id}'")
        chat = self.db.fetchone()
        columns = self.db.get_columns("chats")
        data = {columns[i][0]: chat[i] for i in range(len(chat))}
        self.chat = [Chat(**chat) for chat in data]
        self.db.conn.close()

    def to_dict(self) -> dict:
        obj = self.__dict__.copy()
        obj["reminders"] = [reminder.to_dict() for reminder in obj["reminders"]]
        for key in list(obj.keys()):
            if isinstance(obj[key], datetime):
                obj[key] = obj[key].isoformat()
            elif isinstance(obj[key], Chat):
                obj[key] = obj[key].to_dict()
            if type(obj[key]) not in [str, int, float, list, dict, tuple, set]:
                del obj[key]
        return obj

    def update(self):
        self.db = HerokuDB()
        user_data = self.to_dict()
        users_columns = self.db.get_columns("users")
        to_add = {col: user_data[col] for col in user_data.keys() if col in users_columns}
        self.db.update("users", f"telegram_id = '{self.telegram_id}'", data=to_add)
        chats_columns = self.db.get_columns("chats")
        to_add = {col: user_data["chat"][col] for col in user_data["chat"].keys() if col in chats_columns}
        to_add["telegram_id"] = self.telegram_id
        self.db.update("chats", f"telegram_id = '{self.telegram_id}'", data=to_add)
        reminders_columns = self.db.get_columns("reminders")
        for reminder in user_data["reminders"]:
            to_add = {col: reminder[col] for col in reminder.keys() if col in reminders_columns}
            to_add["telegram_id"] = self.telegram_id
            self.db.update(
                "reminders",
                f"telegram_id = '{self.telegram_id}' AND reminder_id = '{reminder['reminder_id']}'",
                persist=True,
                data=to_add,
            )
        self.db.conn.close()


class Users:
    def get_user(self, telegram_id: Union[str, int]):
        self.db = HerokuDB()
        if type(telegram_id) == int:
            telegram_id = str(telegram_id)
        user = None
        self.db.cursor.execute(f"SELECT * FROM users WHERE telegram_id = '{telegram_id}'")
        content = self.db.cursor.fetchone()
        if content:
            columns = self.db.get_columns("users")
            user_data = {columns[i]: content[i] for i in range(len(columns))}
            user = User(**user_data)
        self.db.conn.close()
        return user

    def add_user(self, user: User):
        if not user.telegram_id:
            raise Exception("User telegram_id parameter must be not null.")

        if type(user.telegram_id) == int:
            user.telegram_id = str(user.telegram_id)

        if not self.get_user(user.telegram_id):
            self.db.connect()
            columns = self.db.get_columns("users")
            user_data = user.to_dict()
            to_add = {col: user_data[col] for col in user_data.keys() if col in columns}
            self.db.insert("users", list(to_add.values()), list(to_add.keys()))
            self.db.conn.close()
            return True
        return False
