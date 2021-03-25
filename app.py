import os
import telebot
import requests

from datetime import datetime

from flask_restful import Api
from flask import Flask, request

from models.alice import controller
from utils.datetime_tools import utc2local
from utils.database import HerokuDB


ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

app = Flask(__name__)
api = Api(app)

tkn = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(tkn)

alice = controller


@app.route("/alice-webhook", methods=["POST"])
def alice_webhook():
    data = request.json
    try:
        chat_id = data["message"]["chat"]["id"]
        alice.user_id = chat_id

        message_text = None
        message_image = None
        if "text" in data["message"]:
            message_text = data["message"]["text"]
        elif "photo" in data["message"]:
            image_id = bot.get_file(data["message"]["photo"][-1]["file_id"])
            image_bytes = requests.get(f"https://api.telegram.org/file/bot{tkn}/{image_id}").content
            if "temp" not in os.listdir():
                os.mkdir("temp")
            message_image = f"{os.getcwd()}/temp/IMG-{datetime.now().isoformat()}.jpg".replace("\\", "/")
            with open(message_image, "wb") as f:
                f.write(image_bytes)
            if "caption" in data["message"]:
                message_text = data["message"]["caption"]

        if message_text:
            bot.send_chat_action(chat_id, "typing")
            answers = alice.get_response(message_text, image=message_image)
            for answer in answers:
                if answer[0] == "msg":
                    # print(message.chat.id)
                    bot.send_message(chat_id, answer[1])
                elif answer[0] == "img":
                    bot.send_photo(chat_id, photo=answer[1])
                elif answer[0] == "doc":
                    bot.send_document(chat_id, document=answer[1])
                elif answer[0] == "video":
                    bot.send_video(chat_id, document=answer[1])

        if "voice" in data["message"]:
            bot.send_message(chat_id, "Poxa, sinto muito. Ainda não sei reconhecer áudios.")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        bot.send_message(ADMIN_USER_ID, error_msg)

    alice.user_id = None
    return {"status": 200}


@app.route("/alice-sender", methods=["POST"])
def alice_sender():
    db = HerokuDB()
    data = request.json
    reminder_id = data["reminders_notified"][0]["id"]
    db.cursor.execute(f"SELECT telegram_id FROM reminders WHERE reminder_id = '{reminder_id}'")
    r = db.cursor.fetchall()
    telegram_id = r[0][0]
    title = data["reminders_notified"][0]["title"]
    reminder_datetime = utc2local(datetime.strptime(data["reminders_notified"][0]["time_tz"], "%H:%M:%S"), normalize=True)
    reminder_time = reminder_datetime.strftime("%H:%M")
    if data["reminders_notified"][0]["notes"] == "reminder":
        msg = "Olá! Passando para te avisar do seu lembrete "
        if title != "Reminder":
            msg += f'"{title}" '
        msg += f"programado para as {reminder_time}."
        bot.send_message(telegram_id, msg)
        db.cursor.execute(f"DELETE FROM reminders WHERE reminder_id = '{reminder_id}'")
        db.conn.commit()
        return {"status": 200}


@app.after_request
def add_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    return response


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="8080")
