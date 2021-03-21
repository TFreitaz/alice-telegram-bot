import os
import psycopg2


HEROKU_DB_URL = os.getenv("HEROKU_DB_URL")


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

    def insert(self, table, values, columns=[]):
        cmd = f"INSERT INTO {table}"
        if len(columns) > 0:
            cmd += "(" + ", ".join(columns) + ")"
        cmd += " VALUES (" + ", ".join(map(set_value, values)) + ");"
        self.cursor.execute(cmd)
        self.conn.commit()

    def get_columns(self, table: str):
        self.cursor.execute(f"SELECT Column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'")
        return [item[0] for item in self.cursor.fetchall()]
