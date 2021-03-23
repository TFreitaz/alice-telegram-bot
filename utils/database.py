import os
import telebot
import psycopg2


HEROKU_DB_URL = os.getenv("HEROKU_DB_URL")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


def zlog(message):
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    bot.send_message(ADMIN_USER_ID, message)


def create_cmd(table, columns):
    return f"CREATE TABLE {table}(" + ", ".join([f"{col} varchar" for col in columns]) + ");"


def set_value(value: str):
    if type(value) != str:
        value = str(value)
    value = value.replace("'", "")
    return f"'{value}'"


class HerokuDB:
    def __init__(self):
        self.connect()

    def connect(self):
        # self.conn = psycopg2.connect(database=DATABASE, host=HOST, password=PASSWORD, user=USER, port=PORT)
        self.conn = psycopg2.connect(HEROKU_DB_URL)
        self.cursor = self.conn.cursor()

    def insert(self, table, **fields):
        columns = fields.get("columns", [])
        values = fields.get("values", [])
        data = fields.get("data", {})

        if data:
            columns = list(data.keys())
            values = list(data.values())

        cmd = f"INSERT INTO {table}"
        if len(columns) > 0:
            cmd += "(" + ", ".join(columns) + ")"
        cmd += " VALUES (" + ", ".join(map(set_value, values)) + ");"
        self.cursor.execute(cmd)
        self.conn.commit()

    def update(self, table, condition, persist=False, **fields):
        columns = fields.get("columns", [])
        values = fields.get("values", [])
        data = fields.get("data", {})

        if columns and values:
            data = {columns[i]: values[i] for i in range(len(values))}

        if persist:
            zlog(f"SELECT * FROM {table} WHERE {condition}")
            self.cursor.execute(f"SELECT * FROM {table} WHERE {condition}")
            count = len(self.cursor.fetchall())
            if not count:
                self.insert(table, data=data)
                return

        cmd = f"UPDATE {table} SET "
        cmd += ", ".join([f"{key} = '{data[key]}'" for key in data.keys()])
        cmd += f" WHERE {condition}"

        zlog(cmd)

        self.cursor.execute(cmd)
        self.conn.commit()

    def get_columns(self, table: str):
        self.cursor.execute(f"SELECT Column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'")
        return [item[0] for item in self.cursor.fetchall()]
