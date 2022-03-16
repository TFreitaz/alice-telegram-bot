import os
import re
import json
import pytz
import telebot
import requests
import numpy as np

from datetime import datetime, timedelta

from utils.database import HerokuDB
from utils.investments import Stocks
from utils.user_manager import Reminder
from utils.datetime_tools import fromisoformat, local2utc, next_weekday, utc2local, weekdays

from chatbot.controller import Controller
from chatbot.utils import remove_comms, clear_text, get_link, flip_coin
from chatbot.features.purchases import find_product, estimate_unity

# from utils.image_tools import cartoon_generator

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = int(str(os.getenv("ADMIN_USER_ID")))

utc_tz = pytz.timezone("UTC")
local_tz = pytz.timezone("Brazil/East")


def zlog(message):
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    bot.send_message(ADMIN_USER_ID, message)


controller = Controller()


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
    if controller.user.nickname and flip_coin(0.7):
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
    comms=["comprar"],
    description="Registrar itens na lista de compras do usuário",
    user_inputs=["item 1 (quantidade)", "item 2 (quantidade)", "item 3 (quantidade)"],
)
def root_shopping_list_registry(message, **fields):
    answers = []

    db = HerokuDB()
    now = utc2local(datetime.now()).isoformat()

    message = message.replace("/comprar", "")

    re_product_name = r"(\w+(\s\w+)*)"
    re_product_quantity = r"(\d+([.,]\d+)?)"
    re_product_unity = r"(\w*)"
    re_product_details = f"\\({re_product_quantity}\\s*{re_product_unity}\\)"
    re_separetor = r"[,;]*"
    re_product = f"{re_product_name}(\\s{re_product_details})?{re_separetor}"
    itermsg = re.finditer(re_product, message)

    answer = "Foram adicionados à lista:"

    for s in itermsg:
        item = find_product(s.group(1), controller.user_id)
        quantity = s.group(4)
        quantity_ef = quantity if quantity is not None else 1
        unity = s.group(6)

        db.insert("shopping_list", values=(controller.user_id, item, quantity_ef, unity, now))

        if quantity:
            if unity:
                answer += f"\n - {quantity} {unity} de {item}"
            else:
                answer += f"\n - {quantity} {item}"
        else:
            answer += f"\n - {item}"

    answers.append(("msg", answer))

    return answers


@controller.add_adapter(
    comms=["comprei"],
    description="Registrar itens comprados pelo usuário",
    user_inputs=["item 1 (quantidade)", "item 2 (quantidade)", "item 3 (quantidade)"],
)
def purchase_registry(message, **fields):
    answers = []

    db = HerokuDB()
    now = utc2local(datetime.now())
    now_str = now.strftime("%d/%m/%Y às %H:%M")

    message = message.replace("/comprei", "")

    re_product_name = r"(\w+(\s\w+)*)"
    re_product_quantity = r"(\d+([.,]\d+)?)"
    re_product_unity = r"(\w*)"
    re_product_details = f"\\({re_product_quantity}\\s*{re_product_unity}\\)"
    re_separetor = r"[,;]*"
    re_product = f"{re_product_name}(\\s{re_product_details})?{re_separetor}"
    itermsg = re.finditer(re_product, message)

    answer = f"Foram comprados no dia {now_str}:"

    for s in itermsg:
        item = find_product(s.group(1), controller.user_id)
        quantity = s.group(4)
        quantity_ef = quantity if quantity is not None else 1
        unity = s.group(6)

        db.insert("purchases", values=(controller.user_id, item, quantity_ef, unity, now))

        if quantity:
            if unity:
                answer += f"\n - {quantity} {unity} de {item}"
            else:
                answer += f"\n - {quantity} {item}"
        else:
            answer += f"\n - {item}"

    answers.append(("msg", answer))

    return answers


@controller.add_adapter(comms=["mostrar_compras"], reqs=["mostrar", "compras"], description="Mostrar última compra de cada item.")
def show_purchases(message, **fields):
    answers = []

    db = HerokuDB()

    db.cursor.execute(
        f"""
        SELECT * FROM purchases 
        WHERE
            telegram_id='{controller.user_id}'
        AND datetime=(
            SELECT MAX(datetime) FROM purchases AS f
            WHERE
                telegram_id='{controller.user_id}'
            AND
                purchases.item=f.item)
        ORDER BY datetime DESC"""
    )
    r = db.cursor.fetchall()

    answer = "Estas são suas últimas compras:\n"
    last_date = None
    for purchase in r:
        _, item, quantity, unity, _ = purchase
        if last_date is None or last_date != purchase[-1].strftime("%d/%m/%Y"):
            last_date = purchase[-1].strftime("%d/%m/%Y")
            answer += f"\n{last_date}"
        if quantity:
            if unity:
                answer += f"\n - {quantity} {unity} de {item}"
            else:
                answer += f"\n - {quantity} {item}"
        else:
            answer += f"\n - {item}"

    answers.append(("msg", answer))
    return answers


@controller.add_adapter(
    comms=["sugerir_compras"], description="Sugerir itens a serem comprados de acordo com suas compras passadas."
)
def groceries_list(message, **fields):

    answers = []

    db = HerokuDB()

    db.cursor.execute(
        f"""
        SELECT * FROM purchases 
        WHERE
            telegram_id='{controller.user_id}'
        ORDER BY datetime ASC"""
    )
    r = db.cursor.fetchall()

    items = {}
    for raw in r:
        item = raw[1]
        if item not in items:
            items[item] = []
        items[item].append({"date": raw[4], "quantity": raw[2]})

    answer = "Sugestões de compras:\n"

    for item_name in items:
        ratios = []
        deltas = []
        if len(items[item_name]) <= 1:
            continue
        item = items[item_name]
        unity = None
        for i in range(len(item)):
            if item[i]["quantity"] == "None":
                item[i]["quantity"] = 1
        for i in range(1, len(item)):
            delta_date = (item[i]["date"] - item[i - 1]["date"]).days
            q = float(item[i - 1]["quantity"])
            ratio = delta_date / q
            ratios.append(ratio)
            deltas.append(delta_date)
        u = np.mean(ratios)
        d = np.mean(deltas)
        delta_now = (datetime.today() - item[-1]["date"]).days + d
        qtd = int(round(delta_now / u - float(item[-1]["quantity"]), 0))
        if qtd > 0:
            answer += f"\n- {qtd}"
            unity = estimate_unity(controller.user_id, item_name, qtd)
            if unity and unity != "None" and unity is not None:
                answer += f" {unity} de"
            answer += f" {item_name}"

    db.cursor.execute(
        f"""
        SELECT
            item, quantity, unity FROM shopping_list 
        WHERE
            telegram_id='{controller.user_id}'
        ORDER BY datetime ASC"""
    )
    r = db.cursor.fetchall()

    if len(r) > 0:
        answer += "\n\ne aqui está sua lista de compras:\n"

        for item_name, quantity, unity in r:
            if quantity and quantity != "None" and float(quantity) > 0:
                answer += f"\n- {quantity}"
                if unity and unity != "None":
                    answer += f" {unity} de"
                answer += f" {item_name}"
    answers.append(("msg", answer))
    return answers


@controller.add_adapter(comms=["mostrar_lembretes"], reqs=["reminders"], description="Mostrar seus lembretes.")
def ShowReminders(message, **fields):
    answers = []

    controller.user.get_reminders()

    if controller.user.reminders:

        answer = "Estes são os seus lembretes:\n\n"
        if controller.user.nickname and flip_coin(0.3):
            answer = f"{controller.user.nickname}, estes são os seus lembretes:\n\n"

        answer += "\n".join(
            f"{fromisoformat(reminder.remind_at).strftime('%d/%m/%Y às %H:%M')} - {reminder.title}"
            for reminder in controller.user.reminders
        )

    else:
        answer = "Você não tem lembretes marcados."
        if controller.user.nickname and flip_coin(0.3):
            answer = f"{controller.user.nickname}, você não tem lembretes marcados."

    answers.append(("msg", answer))

    return answers


@controller.add_adapter(
    reqs=["reminder"],
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
    payload = {"timezone": "UTC", "notes": "reminder"}

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
        else:
            for weekday in weekdays:
                if controller.match(reqs=[weekday]):
                    reminder_date = next_weekday(now, weekday).strftime("%Y-%m-%d")
                    break
            else:
                if controller.match(reqs=["fim", "semana"]):
                    reminder_date = next_weekday(now, "sábado").strftime("%Y-%m-%d")

    if not (hh and mm):
        mm = "00"
        if controller.match(reqs=["manhã"]):
            hh = "09"
        elif controller.match(reqs=["tarde"]):
            hh = "15"
        elif controller.match(reqs=["noite"]):
            hh = "20"
        elif controller.match(reqs=["madrugada"]):
            hh = "02"
        elif controller.match(reqs=["antes", "almoço"]):
            hh = "11"
        elif controller.match(reqs=["depois", "almoço"]):
            hh = "13:00"
        elif re.search(r"\d*", message):
            hh = re.search(r"\d*", message).group()
            if len(hh) == 1:
                hh = "0" + hh

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
        reminder_datetime = f'{aaaa}-{MM}-{dd} {payload["time_tz"]}'
    elif reminder_date:
        reminder_datetime = f'{reminder_date} {payload["time_tz"]}'
    else:
        reminder_datetime = now.strftime("%Y-%m-%d") + f' {payload["time_tz"]}'

    reminder_datetime = datetime.strptime(reminder_datetime, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.timezone("Brazil/East"))
    if (reminder_datetime - now).days < 0:
        reminder_datetime = reminder_datetime + timedelta(days=1)
    payload["date_tz"] = reminder_datetime.strftime("%Y-%m-%d")

    r = requests.post(url, json=payload, headers=header)

    if r.ok:
        resp = r.json()
        reminder_datetime = utc2local(datetime.strptime(f'{resp["date_tz"]} {resp["time_tz"]}', "%Y-%m-%d %H:%M:%S"))
        reminder_timer = reminder_datetime.strftime("%H:%M")
        reminder_date = reminder_datetime.strftime("%d/%m/%Y")
        if name:
            name_text = f", {name}"
        answer = f'Prontinho{name_text}! Lembrete "{resp["title"]}" programado para as {reminder_timer}h de {reminder_date}.'
        remind_at = reminder_datetime.isoformat()
        created_at = utc2local(fromisoformat(resp["created_at"][:-1]))
        updated_at = utc2local(fromisoformat(resp["updated_at"][:-1]))
        remind = Reminder(
            reminder_id=str(resp["id"]), title=resp["title"], remind_at=remind_at, created_at=created_at, updated_at=updated_at
        )
        controller.user.reminders.append(remind)
        controller.user.update()
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
    pokemon_id = re.search(r"pokemon\s[\w\-]*", clear_text(message)).group().split()[1].lower()
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
    if controller.user.nickname and flip_coin(0.7):
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
        if controller.user.nickname and flip_coin(0.3):
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
            if controller.user.nickname and flip_coin():
                name_text = f", {controller.user.nickname}"
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
    if controller.user.nickname and flip_coin():
        name_text = f", {controller.user.nickname}"
    if len(links) > 0:
        for link in links:
            source = re.search(r"\w*\.(com|net)", link).group().split(".")[0]
            db.insert("links", values=[controller.user_id, source, link], columns=["user_id", "source", "link"])
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
    if controller.user.nickname and flip_coin():
        name_text = f", {controller.user.nickname}"
    answer = f"Sinto muito{name_text}. Não entendi."
    answers.append(("msg", answer))
    return answers
