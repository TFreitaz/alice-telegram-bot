import os
import psycopg2
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

HEROKU_DB_URL = os.getenv("HEROKU_DB_URL")

conn = psycopg2.connect(HEROKU_DB_URL)
cursor = conn.cursor()

cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")
tables = [r[0] for r in cursor.fetchall()]

print("INICIALIZANDO BANCO DE DADOS POSTGRESQL...\n")

if "users" not in tables:
    print("Criando tabela users")
    cursor.execute(
        "CREATE TABLE users(telegram_id varchar, nickname varchar, city varchar, state varchar, PRIMARY KEY (telegram_id));"
    )

if "reminders" not in tables:
    print("Criando tabela reminders")
    cursor.execute(
        "CREATE TABLE reminders(telegram_id varchar, title varchar, reminder_id varchar, remind_at varchar, created_at varchar, updated_at varchar,  PRIMARY KEY (reminder_id));"
    )

if "chats" not in tables:
    print("Criando tabela chats")
    cursor.execute(
        "CREATE TABLE chats(telegram_id varchar, last_message varchar, last_message_at varchar, PRIMARY KEY (telegram_id));"
    )

if "links" not in tables:
    print("Criando tabela links")
    cursor.execute("CREATE TABLE links(user_id varchar, source varchar, link varchar, tags varchar);")

if "purchases" not in tables:
    print("Criando tabela purchases")
    cursor.execute(
        "CREATE TABLE purchases(telegram_id varchar, item varchar, quantity varchar, unity varchar, datetime TIMESTAMP);"
    )

if "notes" not in tables:
    print("Criando tabela notes")
    cursor.execute("CREATE TABLE notes(telegram_id varchar, bucket varchar, note varchar, datetime TIMESTAMP);")

print("SALVANDO ALTERAÇÕES...")
conn.commit()
print("BANCO DE DADOS CRIADO!")
