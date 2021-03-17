import os

from chatterbot import ChatBot

MONGO_DB_URI = os.getenv("MONGO_DB_URI")

chatter = ChatBot(
    "Alice",
    storage_adapter="chatterbot.storage.MongoDatabaseAdapter",
    logic_adapters=["chatterbot.logic.BestMatch"],
    database_uri=MONGO_DB_URI,
)
