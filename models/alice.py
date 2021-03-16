import os
import re
import json
import pytz
import string
import telebot
import requests
import unidecode

from datetime import datetime, timedelta

from utils.database import DataBase
from utils.investments import Stocks
from utils.image_tools import cartoon_generator

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")


class Helper:
    def __init__(self):
        self.public_adapters = []
        self.admin_adapters = []


class Controller:
    def __init__(self):
        self.adapters = []
        self.classes = {
            "agradecimento": ["valeu", "obrigado", "obrigada", "brigado", "vlw"],
            "alarm": [
                "alarm",
                "alarme",
                "remind",
                "reminder",
                "lembre",
                "lembrete",
                "lembra",
                "avisa",
                "avise",
                "diga",
                "alerta",
                "alerte",
                "chame",
                "chama",
                "lembrar",
                "avisar",
                "chamar",
            ],
            "amb": [
                "ambulancia",
                "medico",
                "doente",
                "hospital",
                "clinica",
                "mal",
                "desmaio",
                "desmaiei",
                "desmaiou",
                "acidente",
                "acidentou",
                "acidentado",
                "quebrou",
                "morrendo",
                "morrer",
                "infarto",
                "enfarto",
                "avc",
                "quebrou",
                "quebrei",
                "pulso",
                "pulsação",
            ],
            "audio": ["audio", "musica", "mp3", "som", "music"],
            "bitcoin": ["bitcoin", "btc", "btcbrl", "criptomoeda", "bitcoins", "cripo", "criptomoedas"],
            "calendario": ["eventos", "agenda", "calendario", "compromissos", "compromisso", "evento"],
            "cancelar": ["cancelar", "cancela", "outro", "errado"],
            "cinemais": ["cinemais"],
            "clima": ["clima", "tempo", "previsao", "weather", "chover", "chuva", "sol", "temperatura"],
            "compra": ["comprar", "compra"],
            "cop": [
                "policia",
                "crime",
                "assalto",
                "sequestro",
                "roubo",
                "roubaram",
                "sequestraram",
                "assaltaram",
                "assaltou",
                "policial",
                "sequestrar",
                "roubar",
                "viatura",
                "assaltado",
            ],
            "covid": ["covid", "covid19", "corona", "coronavirus", "sarscov2", "cov"],
            "download": ["download", "baixar", "baixe"],
            "duvida": ["duvida", "questionamento", "pergunta", "saber", "sabe", "pregunta"],
            "emergencia": ["emergencia", "help", "socorro", "ajuda"],
            "event": ["evento", "compromisso", "eventos"],
            "female": ["feminino", "female", "f", "w", "mulher", "femea", "woman"],
            "filme": ["filme", "filmes", "movie", "movies", "cinema", "cinemas"],
            "fireman": ["bombeiro", "bombeiros", "incendio", "fogo", "explosao"],
            "forecast": ["previsao", "estimativa"],
            "holiday": ["feriado", "ferias", "folga", "feriados"],
            "info": [
                "informacao",
                "info",
                "informativo",
                "relatorio",
                "atualizacao",
                "informe",
                "fale",
                "informa",
                "relate",
                "relacao",
            ],
            "intenção": ["quero", "desejo", "preciso", "vou"],
            "kinoplex": ["kinoplex"],
            "limit": ["limit", "limite", "marca", "marcacao"],
            "loja": ["lojas", "estabelecimentos", "loja", "estabelecimento"],
            "male": ["masculino", "male", "m", "homem", "macho", "man"],
            "mostrar": [
                "ver",
                "saber",
                "exibir",
                "mostrar",
                "classe",
                "classifico",
                "classificacao",
                "classificado",
                "classifica",
                "classificar",
                "qualifica",
                "preco",
                "custo",
                "lucro",
                "cotacao",
                "vender",
                "vende",
                "vendo",
                "venda",
            ],
            "movie": ["filme", "filmes"],
            "nao": ["nao", "negativo", "n"],
            "next": ["proximo", "proximos", "seguir", "futuro", "futuros", "previsto", "previstos"],
            "news": ["noticia", "noticias", "novidade", "novidades", "jornal"],
            "notify": ["notificacao", "notificacoes", "notificar", "alerta", "alertas"],
            "playlist": ["playlist"],
            "pokemon": ["pokemon"],
            "praca": ["praca", "novo", "menor"],
            "quest": [
                "qual",
                "quais",
                "como",
                "pode",
                "mostre",
                "poderia",
                "gostaria",
                "quero",
                "preciso",
                "que",
                "quando",
                "onde",
                "quanto",
                "quantos",
                "algum",
                "alguns",
            ],
            "rank": ["rank", "rankin", "top", "melhor", "melhores", "mais", "best"],
            "sair": ["sair"],
            "shopping": ["shopping", "shoppings"],
            "sim": ["sim", "positivo", "claro", "isso", "confirma", "confirmo", "s", "sm"],
            "stock": ["stock", "acoes", "acao", "empresa", "empresas", "investimentos", "investimento"],
            "teste": [
                "test",
                "teste",
                "testes",
                "testar",
                "testando",
                "testo",
                "testei",
                "testezinho",
                "checar",
                "check",
                "checando",
                "checkando",
            ],
            "today": ["today", "hoje", "agora"],
            "turnoff": ["desativar", "off", "parar", "pare", "desative"],
            "turnon": ["ativar", "ligar", "começar", "start", "ative", "ligue"],
            "urashopping": ["uberaba", "center", "antigo", "velho", "maior"],
            "venda": ["vender", "vende", "venda"],
            "video": ["video", "filme", "clip", "trailer"],
        }
        self.classification = []
        self.commands = []
        self.helper = Helper()
        self.user_id = None

    def add_adapter(
        self, reqs=None, comms=None, only_admin=False, after_classification=[], after_commands=[], description="", user_inputs=[]
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
        for word in self.classes.keys():
            if any(x in self.classes[word] for x in ClearText(message).split()):
                self.classification.append(word)

        for word in message.split():
            if word.startswith("/"):
                self.commands.append(f'{ClearText(word).replace(" ", "")}')

    def match(self, reqs=None, comms=None):
        if reqs:
            if all(x in self.classification for x in reqs):
                return True
        if comms:
            if all(x in self.commands for x in comms):
                return True

        return False

    def get_response(self, text=None, image=None):
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
                return self.send(ans)
        # return self.send([("msg", json.dumps(self.classification)), ("msg", json.dumps(self.commands))])

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


def remove_comms(text):
    return " ".join([word for word in text.split() if not word.startswith("/")])


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
    answer.append(("msg", "Tudo bem. Como posso te ajudar então?"))
    return answer


@controller.add_adapter(
    reqs=["alarm"],
    comms=["lembrete"],
    description="Programar lembrete",
    user_inputs=['"nome do lembrete"', "data", "horário"],
)
def Reminder(message, **fields):

    token = os.getenv("REMINDER_API_TOKEN")
    answers = []

    url = "https://reminders-api.com/api/applications/48/reminders"

    header = {"Authorization": f"Bearer {token}"}
    payload = {"timezone": "UTC", "notes": str(controller.user_id)}

    now = datetime.now(pytz.timezone("Brazil/East"))

    hh = mm = None
    dd = MM = aaaa = None

    for word in message.split():
        if ":" in word:
            temp = word.split(":")
            if len(temp) in [2, 3]:
                temp = [re.search(r"\d*", val).group() for val in temp]
                if (temp[0] and temp[0].isnumeric) and (temp[1] and temp[1].isnumeric):
                    if 0 <= int(temp[0]) <= 23 and 0 <= int(temp[1]) <= 59:
                        hh = str(int(temp[0]) + 3)
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

    temp = message.split('"')
    if len(temp) >= 3:
        payload["title"] = temp[1]
    else:
        payload["title"] = "Reminder"

    if hh and mm:
        payload["time_tz"] = f"{hh}:{mm}"
    else:
        payload["time_tz"] = (now + timedelta(hours=1)).strftime("%H:%M")

    if dd and MM and aaaa:
        payload["date_tz"] = f"{aaaa}-{MM}-{dd}"
    else:
        reminder_datetime = now.strftime("%Y-%m-%d") + f' {payload["time_tz"]}'
        reminder_datetime = datetime.strptime(reminder_datetime, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.timezone("Brazil/East"))
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
        answer = f'Pronto! Lembrete "{resp["title"]}" programado para as {hh}:{mm}h de {dd}/{MM}/{aaaa}.'

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


@controller.add_adapter(
    reqs=["cartoon"], comms=["cartoon"], only_admin=True, description="Gerar versão cartoon de uma imagem", user_inputs=["imagem"]
)
def Cartoon(message, **fields):
    answers = []

    image = fields.get("image", None)

    if not image:
        answer = "Me mande uma imagem para eu transformar em cartoon!"
        answers.append(("msg", answer))
    else:
        answer1 = "Aqui está seu cartoon! Espero que goste ^^"
        k = 9
        numbers = re.findall(r"\d+", message)
        if len(numbers) > 0:
            k = numbers[0]

        answer2 = cartoon_generator(image, k)

        answers.append(("msg", answer1))
        answers.append(("img", answer2))
    return answers


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
    answer = "Se precisar, é só chamar."
    blocks = ["agradecimento"]
    controller.classification = list(filter(lambda a: a not in blocks, controller.classification))
    answers.append(("msg", answer))
    return answers


@controller.add_adapter(
    comms=["secret", "link", "generate"], only_admin=True, description="Salvar link em modo secreto", user_inputs=["link"]
)
def Secred_link_generate(message, **fields):
    answers = []
    log = ""
    db = DataBase()
    try:
        n = int(re.findall(r"\d+", message)[0])
    except Exception:
        log = "Não identifiquei o número."
    else:
        cmd = f"SELECT link FROM links ORDER BY random() LIMIT {n}"
        db.cursor.execute(cmd)
        links = db.cursor.fetchall()
        if len(links) == 0:
            log += "Não encontrei nenhum link salvo."
        else:
            answer1 = "Aqui está!\n"
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
def Secred_link_add(message, **fields):
    answers = []
    db = DataBase()
    links = get_link(message)
    log = ""
    if len(links) > 0:
        for link in links:
            source = re.search(r"\w*\.(com|net)", link).group().split(".")[0]
            db.insert("links", [controller.user_id, source, link], ["user_id", "source", "link"])
        db.conn.commit()
        answer1 = "Prontinho!"
    else:
        answer1 = "Não recebi nenhum link."
    db.conn.close()
    answers.append(("msg", answer1))
    if log:
        answers.append(("msg", log))
    return answers


@controller.add_adapter(comms=["invert"], description="Inverter um texto", user_inputs=["texto"])
def Invert(message):
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


@controller.add_adapter(reqs=[], comms=[])
def Undefined(message, **fields):
    answers = []
    answer = "Sinto muito, mas não entendi."
    answers.append(("msg", answer))
    return answers
