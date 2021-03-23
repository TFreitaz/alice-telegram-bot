import os
import re
import json
import pytz
import string
import telebot
import requests
import unidecode

from datetime import datetime, timedelta

from utils.investments import Stocks
from utils.user_manager import User, Users, Reminder
from utils.database import HerokuDB

# from utils.image_tools import cartoon_generator

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = int(str(os.getenv("ADMIN_USER_ID")))


def zlog(message):
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    bot.send_message(ADMIN_USER_ID, message)


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
        for word in self.classes.keys():
            if any(x in self.classes[word] for x in ClearText(message).split()):
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


controller = Controller()

# # Utils


def ClearText(text):
    # stemmer = nltk.stem.RSLPStemmer()
    if type(text) == str:
        x = text.split()
    else:
        x = text
    if type(x) == list:
        newx = list()
        for word in x:
            w = word.lower()
            w = unidecode.unidecode(w)
            for c in list(string.punctuation):
                w = w.replace(c, " ")
            if len(w) > 0:
                if w[-1] == " ":
                    w = w[:-1]
                # print('{} -> {}'.format(word, w))
            newx.append(w)
        text = " ".join(newx)
    else:
        text = " ".join(text)
    return text


def get_link(ans):
    links = []
    for term in ans.split():
        if ".com" in term or "http" in term:
            links.append(term)
    return links


def local2utc(dt):
    return dt.replace(tzinfo=pytz.timezone("Brazil/East")).astimezone(pytz.timezone("UTC"))


def remove_comms(text):
    return " ".join([word for word in text.split() if not word.startswith("/")])


def utc2local(dt):
    return dt.replace(tzinfo=pytz.timezone("UTC")).astimezone(pytz.timezone("Brazil/East"))


@controller.add_adapter(comms=["help"])
def Help(message, **fields):
    answers = []
    answer = "Esta é a lista de funções e comandos que eu conheço:\n\n"
    for adapter in controller.helper.public_adapters:
        answer += f"- {adapter['description']}"
        if len(adapter["comms"]) > 0:
            user_inputs = ""
            if len(adapter["user_inputs"]) > 0:
                user_inputs = f' <{">, <".join(adapter["user_inputs"])}>'
            answer += f' [{" ".join(["/" + comm for comm in adapter["comms"]])}{user_inputs}]'
        answer += "\n"
    if controller.user_id == ADMIN_USER_ID:
        answer += "\n- Modo administrador:\n\n"
        for adapter in controller.helper.admin_adapters:
            answer += f"- {adapter['description']}"
            if len(adapter["comms"]) > 0:
                user_inputs = ""
                if len(adapter["user_inputs"]) > 0:
                    user_inputs = f' <{" ".join(adapter["user_inputs"])}>'
                answer += f' [{" ".join(["/" + comm for comm in adapter["comms"]])}{user_inputs}]'
            answer += "\n"
    if answer.endswith("\n"):
        answer = answer[:-1]
    answer += "\n\nPara mais informações, acesse: http://bit.ly/alice-readme"
    answers.append(("msg", answer))
    return answers


# Feature functions


@controller.add_adapter(comms=["start"])
def Start(message, **fields):
    answer = [("msg", "Olá, meu nome é Alice, e estou aqui para ajudar! Se quiser saber o que eu posso fazer, envie /help.")]
    return answer


@controller.add_adapter(reqs=["cancelar"])
def Cancelar(message, **fields):
    answer = []
    name_text = ""
    if controller.user.nickname:
        name_text = ", " + controller.user.nickname
    answer.append(("msg", f"Tudo bem{name_text}. Como posso te ajudar então?"))
    return answer


@controller.add_adapter(comms=["definir_nome"], description="Definir seu nome ou apelido", user_inputs=["nome"])
def SetName(message, **fields):
    answers = []

    name = message.replace("/definir_nome", "").strip()
    while "  " in name:
        name = name.replace("  ", " ")

    if name:
        controller.user.nickname = name
        controller.user.update()

        answer = f"Ok! Vou te chamar de {name}"
        answers.append(("msg", answer))
    else:
        answer = "Não consegui reconhecer um nome. Por favor envie /definir_nome seguido do seu nome ou apelido."
        answers.append(("msg", answer))

    return answers


@controller.add_adapter(
    reqs=["alarm"],
    comms=["lembrete"],
    description="Programar lembrete",
    user_inputs=['"nome do lembrete"', "data", "horário"],
)
def SetReminder(message, **fields):

    token = os.getenv("REMINDER_API_TOKEN")
    answers = []

    name_text = ""
    name = controller.user.nickname

    url = "https://reminders-api.com/api/applications/48/reminders"

    header = {"Authorization": f"Bearer {token}"}
    payload = {"timezone": "UTC", "notes": str(controller.user_id)}

    now = datetime.now(pytz.timezone("Brazil/East"))

    hh = mm = None
    dd = MM = aaaa = None
    reminder_date = None
    reminder_datetime = None

    for word in message.split():
        if ":" in word:
            temp = word.split(":")
            if len(temp) in [2, 3]:
                temp = [re.search(r"\d*", val).group() for val in temp]
                if (temp[0] and temp[0].isnumeric) and (temp[1] and temp[1].isnumeric):
                    if 0 <= int(temp[0]) <= 23 and 0 <= int(temp[1]) <= 59:
                        hh = temp[0]
                        mm = temp[1]

                        if len(hh) == 1:
                            hh = "0" + hh

                        if len(mm) == 1:
                            mm = "0" + mm

                        if len(temp) == 3 and temp[2].isnumeric:
                            if 0 <= int(temp[2]) <= 59:
                                ss = temp[2]

                                if len(ss) == 1:
                                    ss = "0" + ss
                        else:
                            ss = "00"
        if "/" in word:
            temp = word.split("/")
            if len(temp) in [2, 3]:
                temp = [re.search(r"\d*", val).group() for val in temp]
                if (temp[0] and temp[0].isnumeric) and (temp[1] and temp[1].isnumeric):
                    if 1 <= int(temp[0]) <= 31 and 1 <= int(temp[1]) <= 12:
                        dd = temp[0]
                        MM = temp[1]

                        if len(dd) == 1:
                            dd = "0" + dd

                        if len(MM) == 1:
                            MM = "0" + MM

                        now_year = str(now.year)
                        if len(temp) == 3 and temp[2].isnumeric:
                            if int(now_year) <= int(temp[2]) or int(now_year[:-2]) <= int(temp[2]) <= 80:
                                aaaa = temp[2]

                                if len(aaaa) == 2:
                                    aaaa = "20" + ss
                        else:
                            aaaa = now_year

    if not (dd and MM and aaaa):
        if controller.match(reqs=["amanhã"]):
            if 0 <= now.hour <= 4:
                reminder_date = now.strftime("%Y-%m-%d")
            else:
                reminder_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif controller.match(reqs=["hoje"]):
            reminder_date = now.strftime("%Y-%m-%d")

    if not (hh and mm):
        if controller.match(reqs=["manhã"]):
            hh = "08"
            mm = "00"
        elif controller.match(reqs=["tarde"]):
            hh = "16"
            mm = "00"
        elif controller.match(reqs=["noite"]):
            hh = "20"
            mm = "00"
        elif controller.match(reqs=["madrugada"]):
            hh = "02"
            mm = "00"
        elif re.search(r"\d*", message):
            hh = re.search(r"\d*", message).group()
            if len(hh) == 1:
                hh = "0" + hh
            mm = "00"

    temp = message.split('"')
    if len(temp) >= 3:
        payload["title"] = temp[1]
    else:
        payload["title"] = "Reminder"

    if hh and mm:
        time_tz = local2utc(datetime.strptime(f"{hh}:{mm}", "%H:%M")).strftime("%H:%M")
        payload["time_tz"] = time_tz
    else:
        payload["time_tz"] = (now + timedelta(hours=4)).strftime("%H:%M")

    if dd and MM and aaaa:
        payload["date_tz"] = f"{aaaa}-{MM}-{dd}"
    elif reminder_date:
        payload["date_tz"] = reminder_date
    else:
        reminder_datetime = now.strftime("%Y-%m-%d") + f' {payload["time_tz"]}'
        reminder_datetime = datetime.strptime(reminder_datetime, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("Brazil/East"))
        if (reminder_datetime - now).days < 0:
            reminder_datetime = reminder_datetime + timedelta(days=1)
        payload["date_tz"] = reminder_datetime.strftime("%Y-%m-%d")

    r = requests.post(url, json=payload, headers=header)

    if r.ok:
        resp = r.json()
        aaaa, MM, dd = resp["date_tz"].split("-")
        hh, mm, _ = resp["time_tz"].split(":")
        hh = str(int(hh) - 3)
        if len(hh) == 1:
            hh = "0" + hh
        if name:
            name_text = f", {name}"
        answer = f'Prontinho{name_text}! Lembrete "{resp["title"]}" programado para as {hh}:{mm}h de {dd}/{MM}/{aaaa}.'
        reminder_datetime = utc2local(datetime.strptime(f'{resp["date_tz"]} {resp["time_tz"]}', "%Y-%m-%d %H:%M"))
        remind_at = reminder_datetime.isoformat()
        created_at = utc2local(datetime.fromisoformat(resp["created_at"][:-1]))
        updated_at = utc2local(datetime.fromisoformat(resp["updated_at"][:-1]))
        remind = Reminder(
            reminder_id=str(resp["id"]), title=resp["title"], remind_at=remind_at, created_at=created_at, updated_at=updated_at
        )
        controller.user.reminders.append(remind)
    else:
        if name:
            answer = f"{name}, não consegui criar o lembrete. Você pode verificar a mensagem e tentar novamente."
        else:
            answer = "Não consegui criar o lembrete. Você pode verificar a mensagem e tentar novamente."
        answer2 = json.dumps(payload)
        answers.append(("msg", answer2))

    answers.append(("msg", answer))
    return answers


@controller.add_adapter(comms=["sugestao"], description="Enviar uma sugestão para meu desenvolvedor", user_inputs=["texto"])
def Suggestion(message, **fields):
    answers = []

    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    bot.send_message(ADMIN_USER_ID, "SUGESTÃO: " + remove_comms(message))

    answer = "Sua sugestão foi enviada!"
    answers.append(("msg", answer))

    return answers


# @controller.add_adapter(
#     reqs=["cartoon"], comms=["cartoon"], only_admin=True, description="Gerar versão cartoon de uma imagem", user_inputs=["imagem"]
# )
# def Cartoon(message, **fields):
#     answers = []

#     image = fields.get("image", None)

#     if not image:
#         answer = "Me mande uma imagem para eu transformar em cartoon!"
#         answers.append(("msg", answer))
#     else:
#         answer1 = "Aqui está seu cartoon! Espero que goste ^^"
#         k = 9
#         numbers = re.findall(r"\d+", message)
#         if len(numbers) > 0:
#             k = numbers[0]

#         answer2 = cartoon_generator(image, k)

#         answers.append(("msg", answer1))
#         answers.append(("img", answer2))
#     return answers


@controller.add_adapter(
    reqs=["stock", "rank"],
    comms=["stock", "rank"],
    description="Ranking de melhores ações na bolsa de valores nacional",
    user_inputs=["número de ações"],
)
def Stocks_ranking(message, **fields):
    answers = []
    n = int(re.search(r"\d+", message).group())
    if not n:
        n = 5
    stocks = Stocks()
    top = stocks.top_stocks(n)
    answer = ""
    for stock in top:
        name = stock
        if name.endswith(".SA"):
            name = name[:-3]
        answer += f"{name}\n"
        for param in top[stock]:
            answer += f"  - {param}: {top[stock][param]}\n"
    answers.append(("msg", "Aqui está!"))
    answers.append(("msg", answer))
    return answers


@controller.add_adapter(reqs=["pokemon"], comms=["pokemon"], description="Consulta de Pokémon", user_inputs=["nome ou id"])
def Pokemon(message, **fields):
    answers = []
    pokemon_id = re.search(r"pokemon\s[\w\-]*", ClearText(message)).group().split()[1].lower()
    r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
    if r.ok:
        pokemon = json.loads(r.content)
        c = requests.get(pokemon["sprites"]["front_default"])
        with open("pokemon.png", "wb") as f:
            f.write(c.content)
        answer1 = open("pokemon.png", "rb")
        answer2 = f"Nome: {pokemon['forms'][0]['name']}   ID: {pokemon['id']}\n"
        answer2 += "Tipo: " + ", ".join(type_["type"]["name"] for type_ in pokemon["types"]) + "\n"
        answer2 += f"Altura: {pokemon['height']*10} cm   Peso: {pokemon['weight']/10} kg\n"
        answer2 += "Status:\n"
        answer2 += f" - HP: {pokemon['stats'][0]['base_stat']}\n"
        answer2 += f" - Ataque: {pokemon['stats'][1]['base_stat']}\n"
        answer2 += f" - Defesa: {pokemon['stats'][2]['base_stat']}\n"
        answer2 += f" - Ataque especial: {pokemon['stats'][3]['base_stat']}\n"
        answer2 += f" - Defesa especial: {pokemon['stats'][4]['base_stat']}\n"
        answer2 += f" - Velocidade: {pokemon['stats'][5]['base_stat']}\n"
        answer2 += "Habilidades:\n"
        for ability in pokemon["abilities"]:
            answer2 += f" - {ability['ability']['name']}\n"
        answers.append(["img", answer1])
        answers.append(["msg", answer2])
    else:
        answer = f"Não encontrei nada sobre {pokemon_id}"
        answers.append(["msg", answer])
    return answers


@controller.add_adapter(reqs=["agradecimento"])
def Agradecimento(message, **fields):
    answers = []
    name_text = ""
    if controller.user.nickname:
        name_text = f", {controller.user.nickname}"
    answer = f"Disponha{name_text}! Se precisar, é só chamar."
    answers.append(("msg", answer))
    return answers


@controller.add_adapter(
    comms=["secret", "link", "generate"], only_admin=True, description="Salvar link em modo secreto", user_inputs=["link"]
)
def SecredLinkGenerate(message, **fields):
    answers = []
    log = ""
    db = HerokuDB()
    try:
        n = int(re.findall(r"\d+", message)[0])
    except Exception:
        if controller.user.nickname:
            log = f"{controller.user.nickname}, não identifiquei o número."
        else:
            log = "Não identifiquei o número."
    else:
        cmd = f"SELECT link FROM links ORDER BY random() LIMIT {n}"
        db.cursor.execute(cmd)
        links = db.cursor.fetchall()
        if len(links) == 0:
            if controller.user.nickname:
                log = f"{controller.user.nickname}, não encontrei nenhum link salvo."
            else:
                log = "Não encontrei nenhum link salvo."
        else:
            if controller.user.nickname:
                name_text = f"{controller.user.nickname}, "
            answer1 = f"Aqui está{name_text}!\n"
            answer1 += "\n\n".join(link[0] for link in links)
            answers.append(("msg", answer1))
        db.conn.close()
    if log:
        log += "Mensagem: " + message
        answers.append(("msg", log))
    return answers


@controller.add_adapter(
    comms=["secret", "link", "add"],
    only_admin=True,
    description="Gerar conjunto de links secretos salvos",
    user_inputs=["número de links"],
)
def SecredLinkAdd(message, **fields):
    answers = []
    db = HerokuDB()
    links = get_link(message)
    log = ""
    name_text = ""
    if controller.user.nickname:
        name_text = f", {controller.user.nickname}"
    if len(links) > 0:
        for link in links:
            source = re.search(r"\w*\.(com|net)", link).group().split(".")[0]
            db.insert("links", [controller.user_id, source, link], ["user_id", "source", "link"])
        db.conn.commit()
        answer1 = f"Prontinho{name_text}!"
    else:
        answer1 = f"Não recebi nenhum link{name_text}."
    db.conn.close()
    answers.append(("msg", answer1))
    if log:
        answers.append(("msg", log))
    return answers


@controller.add_adapter(comms=["invert"], description="Inverter um texto", user_inputs=["texto"])
def Invert(message, **fields):
    answers = []
    words = message.split()
    words.remove("/invert")
    answer = " ".join(words)[::-1]
    answers.append(("msg", answer))
    return answers


@controller.add_adapter(reqs=["sair"])
def Sair(message, **fields):
    answers = []
    answer = "Espero ter ajudado. Até mais!"
    answers.append(("msg", answer))
    return answers


@controller.add_adapter(reqs=["teste"], comms=["teste"], description="Testar se estou ativa")
def Test(message, **fields):
    answers = []
    answer = "Estou funcionando perfeitamente!"
    answers.append(("msg", answer))
    return answers


@controller.add_adapter()
def Undefined(message, **fields):
    answers = []
    name_text = ""
    if controller.user.nickname:
        name_text = f", {controller.user.nickname}"
    answer = f"Sinto muito{name_text}. Não entendi."
    answers.append(("msg", answer))
    return answers
