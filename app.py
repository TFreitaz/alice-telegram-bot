import os
import telebot
import requests

from datetime import datetime

from models.alice import controller

from flask import Flask, request
from flask_restful import Api

import speech_recognition as sr

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
            r = sr.Recognizer()

            file_info = bot.get_file(data["message"]["voice"]["file_id"])
            downloaded_file = bot.download_file(file_info.file_path)

            try:
                transc = r.recognize_google(downloaded_file)
                bot.send_message(chat_id, transc)
            except Exception:
                bot.send_message(chat_id, "Não consegui reconhecer.")
            # bot.send_voice(chat_id, downloaded_file)
    except Exception as e:
        bot.send_message(ADMIN_USER_ID, str(e))

    alice.user_id = None
    return {"status": 200}


@app.route("/alice-sender", methods=["POST"])
def alice_sender():
    data = request.json
    title = data["reminders_notified"][0]["title"]
    hh, mm, ss = data["reminders_notified"][0]["time_tz"].split(":")
    hh = str(int(hh) - 3)
    if len(hh) == 1:
        hh = "0" + hh
    chat_id = data["reminders_notified"][0]["notes"]
    msg = "Olá! Passando para te avisar do seu lembrete "
    if title != "Reminder":
        msg += f'"{title}" '
    msg += f"programado para as {hh}:{mm}:{ss}."
    bot.send_message(chat_id, msg)
    return {"status": 200}


@app.after_request
def add_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    return response


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="8080")
