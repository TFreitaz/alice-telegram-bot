import random
import string
import unidecode


def flip_coin(true_ratio=0.5):
    return random.random() <= true_ratio


def clear_text(text):
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
