import os
import json

from utils.user_manager import User, Users

from chatbot.utils import clear_text

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = int(str(os.getenv("ADMIN_USER_ID")))


class Helper:
    def __init__(self):
        self.public_adapters = []
        self.admin_adapters = []


class Controller:
    def __init__(self):
        self.adapters = []
        self.classes = json.loads(open("classes.json").read())
        self.classification = []
        self.commands = []
        self.helper = Helper()
        self.user_id = None
        self.user = None

    def add_adapter(
        self, reqs=[], comms=[], only_admin=False, after_classification=[], after_commands=[], description="", user_inputs=[]
    ):
        def create_adapter(func):
            def adapter(message, **fields):
                if self.match(reqs, comms):
                    if (only_admin and self.user_id == ADMIN_USER_ID) or not only_admin:
                        ans = func(message, **fields)
                        self.classification = after_classification
                        self.commands = after_commands
                        return ans

            self.adapters.append(adapter)
            if description:
                adapter_helper = {"description": description, "user_inputs": user_inputs}
                adapter_helper["comms"] = comms if type(comms) == list else []
                if only_admin:
                    self.helper.admin_adapters.append(adapter_helper)
                else:
                    self.helper.public_adapters.append(adapter_helper)
            return adapter

        return create_adapter

    def classific(self, message):
        self.classification = []
        self.commands = []
        if len(message.split('"')) == 3:
            message = message.split('"')[0] + message.split('"')[2]
        for word in self.classes.keys():
            if any(x in self.classes[word] for x in clear_text(message).split()):
                self.classification.append(word)

        for word in message.split():
            if word.startswith("/"):
                self.commands.append(word[1:])

    def match(self, reqs=None, comms=None):
        if reqs:
            if all(x in self.classification for x in reqs):
                return True
        if comms:
            if all(x in self.commands for x in comms):
                return True
        if not (reqs or comms):
            return True

        return False

    def get_response(self, text=None, image=None):
        self.get_user()
        self.classific(text)
        # return self.send([("msg", len(self.adapters))])
        for adap in self.adapters:
            try:
                ans = adap(text, image=image)
            except Exception as e:
                self.classification = []
                self.commands = []
                raise e
            if ans:
                ans += self.postscriptum()
                return self.send(ans)
        # return self.send([("msg", json.dumps(self.classification)), ("msg", json.dumps(self.commands))])

    def get_user(self):
        users = Users()
        self.user = users.get_user(self.user_id)
        if not self.user:
            self.user = User(telegram_id=self.user_id)
            users.add_user(self.user)

    def postscriptum(self):
        answers = []

        if not self.user.nickname:
            answer = "Eu ainda não sei como te chamar."
            answer += " Você pode definir como quer ser chamado usando o comando /definir_nome"
            answer += " seguido do seu nome ou apelido."
            answers.append(("msg", answer))

        return answers

    def send(self, ans):
        self.answer = ans
        return self.answer
