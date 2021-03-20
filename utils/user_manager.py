import os

# import json
import telebot

from typing import List
from datetime import datetime

ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


def zlog(message):
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    bot.send_message(ADMIN_USER_ID, message)


class Chat:
    def __init__(self, **fields):
        self.last_query = fields.get("last_query", "")

    def to_dict(self):
        return self.__dict__


class Reminder:
    def __init__(self, **fields):
        self.id = fields.get("id", "")
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
        self.reminders: List[Reminder] = [Reminder(**reminder) for reminder in fields.get("reminders", "")]

    def to_dict(self) -> dict:
        obj = self.__dict__
        for key in obj.keys():
            if isinstance(obj[key], datetime):
                obj[key] = obj[key].isoformat()
            elif isinstance(obj[key], Chat):
                obj[key] = obj[key].to_dict()
        return obj


# class Users:
#     def get_user(self, telegram_id: Union[str, int]):
#         if type(telegram_id) == int:
#             telegram_id = str(telegram_id)
#         zlog("Usuário pesquisado.")
#         user = users.find_one({"telegram_id": telegram_id})
#         zlog(json.dumps(user))
#         if user:
#             return User(**user)

#     def add_user(self, user: User):
#         zlog("Inserindo usuário.")
#         if not user.telegram_id:
#             raise Exception("User telegram_id parameter must be not null.")

#         if type(user.telegram_id) == int:
#             user.telegram_id = str(user.telegram_id)

#         if not self.get_user(user.telegram_id):
#             users.insert_one(user.to_dict())
#             zlog("Usuário inserido.")
#             return True
#         zlog("Usuário já existente.")
#         return False
