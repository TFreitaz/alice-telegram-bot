import os
import psycopg2
from unidecode import unidecode


HEROKU_DB_URL = os.getenv("HEROKU_DB_URL")

conn = psycopg2.connect(HEROKU_DB_URL)
cursor = conn.cursor()

stopwords = [
    "de",
    "do",
    "em",
    "no",
    "na",
    "ao",
]


def clear_product_name(product_name):
    product_name = unidecode(product_name)
    product_name = product_name.lower()
    product_name = " ".join([word for word in product_name.split() if word not in stopwords])
    return product_name


def find_product(product_name, user_id):
    cursor.execute(f"""SELECT DISTINCT item FROM purchases WHERE telegram_id = '{user_id}'""")
    product_names = [x[0] for x in cursor.fetchall()]
    for name in product_names:
        if clear_product_name(name) == clear_product_name(product_name):
            return name
    return product_name


def estimate_unity(user_id, product_name, quantity):
    cursor.execute(f"""SELECT unity, AVG(CAST(quantity AS DECIMAL)) FROM purchases WHERE item = '{product_name}' GROUP BY unity""")
    r = cursor.fetchall()
    unity = None
    diff = float("inf")
    for u, m in r:
        if abs(quantity - m) < diff:
            unity = u
    return unity
