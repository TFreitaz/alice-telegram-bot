import time
import requests

import pandas as pd
import numpy as np

# import matplotlib.pyplot as plt

from scipy.optimize import minimize_scalar, curve_fit
from datetime import datetime

from utils.database import DataBase


class Stocks:
    def __init__(self):
        self.misseds = []

    def poly1(self, x, a, b):
        # print(x)
        return a * x + b

    def r_squared(self, x, y, popt):
        residuals = y - self.poly1(x, *popt)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared

    def score(self, p):
        p = int(p)
        xdata = np.array(self.df.index)[p:]
        ydata = self.df["Close"].values[p:]
        # if p > len(xdata)-300:
        #    return float('inf')
        popt, pcov = curve_fit(self.poly1, xdata, ydata)
        err = self.r_squared(xdata, ydata, popt)
        if err < 0:
            err = 0.001
        a = popt[0]
        if a < 0:
            a = 0.001
        return 1 / (err * a ** 2 * len(xdata))

    def stock_analyze(self, stock):

        result = {stock: {}}

        # for file in os.listdir(folder):

        today = int(time.mktime(time.strptime(datetime.today().strftime("%d/%m/%Y"), "%d/%m/%Y")))

        try:
            url = f"https://query1.finance.yahoo.com/v7/finance/download/{stock}?period1=0&period2={today}&interval=1d&events=history&includeAdjustedClose=true"
            r = requests.get(url)
            if not r.ok:
                self.misseds.append(stock)
                return
        except Exception:
            self.misseds.append(stock)
            return

        table = r.content.decode().split("\n")
        cols = table[0].split(",")
        data: dict = {col: [] for col in cols}
        for raw in table[1:]:
            for i, value in enumerate(raw.split(",")):
                try:
                    data[cols[i]].append(float(value))
                except Exception:
                    if value == "null":
                        value = None
                    data[cols[i]].append(value)
        self.df = pd.DataFrame(data).dropna()

        name = stock  # file.split('.')[0]
        # df = pd.read_csv(f'{folder}/{file}').dropna()

        last = self.df["Close"][0]
        for i, val in enumerate(self.df["Close"].values):
            if last / val > 3.9:
                self.df = self.df[:i]
                break
            last = val

        xdata = np.array(self.df.index)
        ydata = self.df["Close"].values

        try:
            p = int(minimize_scalar(self.score, bounds=(0, len(xdata) - 300), method="Bounded").x)
        except ValueError:
            return
        popt, pcov = curve_fit(self.poly1, xdata[p:], ydata[p:])

        result[name] = {
            "score": round(1 / self.score(p), 2),
            "period": int(xdata.shape[0] - p),
            "a": popt[0],
            "r²": self.r_squared(xdata[p:], ydata[p:], popt),
        }

        popt, pcov = curve_fit(self.poly1, xdata[p:], ydata[p:])
        y_ = [self.poly1(x, *popt) for x in xdata[p:]]

        # if False:

        #     plt.plot(xdata[p:], ydata[p:])
        #     plt.plot(xdata[p:], y_)
        #     plt.title(name)
        #     plt.savefig("temp_plot.png")

        return

    def top_stocks(self, n):
        db = DataBase()

        cmd = f"SELECT * FROM stocks ORDER BY score DESC LIMIT {n}"
        db.cursor.execute(cmd)
        r = db.cursor.fetchall()

        params = ["score", "period", "a", "r²"]

        top = {}
        for raw in r:
            top[raw[0]] = {param: raw[i + 1] for i, param in enumerate(params)}

        return top
