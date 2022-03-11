import os
import psycopg2


HEROKU_DB_URL = os.getenv("HEROKU_DB_URL")

conn = psycopg2.connect(HEROKU_DB_URL)
cursor = conn.cursor()


def find_product(product_name):
    return product_name
