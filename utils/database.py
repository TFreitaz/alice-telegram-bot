import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")


def create_cmd(table, columns):
    return f"CREATE TABLE {table}(" + ", ".join([f"{col} varchar" for col in columns]) + ");"


def set_value(value: str):
    if type(value) != str:
        value = str(value)
    value = value.replace("'", "")
    return f"'{value}'"


class DataBase:
    def __init__(self):
        self.connect()

    def connect(self):
        # self.conn = psycopg2.connect(database=DATABASE, host=HOST, password=PASSWORD, user=USER, port=PORT)
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cursor = self.conn.cursor()

    def insert(self, table, values, columns=[]):
        cmd = f"INSERT INTO {table}"
        if len(columns) > 0:
            cmd += "(" + ", ".join(columns) + ")"
        cmd += " VALUES (" + ", ".join(map(set_value, values)) + ");"
        self.cursor.execute(cmd)
