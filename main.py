import yfinance as yf
import pandas as pd
import datetime
import json

# Stocks
msft = yf.Ticker('MSFT')
msft_history = msft.history(start='2016-12-31', end='2021-1-1')
apple = yf.Ticker('AAPL')
apple_history = apple.history(start='2016-12-31', end='2021-1-1')
tesla = yf.Ticker('TSLA')
tesla_history = tesla.history(start='2016-12-31', end='2021-1-1')

# Crypto
btc = yf.Ticker('BTC-USD')
btc_history = btc.history(start='2016-12-31', end='2021-1-1')
eth = yf.Ticker('ETH-USD')
eth_history = eth.history(start='2016-12-31', end='2021-1-1')
xmr = yf.Ticker('XMR-USD')
xmr_history = xmr.history(start='2016-12-31', end='2021-1-1')

# Como
gold = yf.Ticker('GC=F')
gold_history = gold.history(start='2016-12-31', end='2021-1-1')
coal = yf.Ticker('MTF=F')
coal_history = coal.history(start='2016-12-31', end='2021-1-1')
brent = yf.Ticker('BZ=F')
brent_history = brent.history(start='2016-12-31', end='2021-1-1')

# print(msft_history.loc['2018-01-02']['Close'])
# print(btc_history)


class Game:

    def __init__(self, year):
        self.start = datetime.datetime.strptime(f"{year}-01-01", "%Y-%m-%d").strftime("%d-%m-%Y")
        self.end = datetime.datetime.strptime(f"{year}-12-31", "%Y-%m-%d").strftime("%d-%m-%Y")
        self.date_list = pd.date_range(start=self.start, end=self.end)
        self.date_list = [d.strftime('%Y-%m-%d') for d in self.date_list]
        self.day = 0
        self.current_day = self.date_list[self.day]
        self.current_weekday = datetime.datetime.strptime(self.current_day, '%Y-%m-%d').strftime('%A')

    def get_asset_data(self, asset):
        price = float("%.2f" % asset.history.loc[self.current_day]['Close'])
        return f"{asset.name} = {price} USD"

    def get_asset_price(self, asset, current_day):
        price = float("%.2f" % asset.history.loc[current_day]['Close'])
        return price

    def next_day(self, days):
        try:
            self.day += days
            self.current_day = self.date_list[self.day]
            self.current_weekday = datetime.datetime.strptime(self.current_day, '%Y-%m-%d').strftime('%A')
        except IndexError:
            self.current_day = self.date_list[-1]

    def encode(self):
        return json.dumps(self.__dict__)





class Asset:

    def __init__(self, name, history):
        self.name = name
        self.history = history


class Portfolio:

    def __init__(self, start_cash):
        self.start_cash = float(start_cash)
        self.cash = self.start_cash
        self.asset_amounts = {'Microsoft': [0, []], 'Apple': [0, []], 'Tesla': [0, []], 'Bitcoin': [0, []], 'Ethereum': [0, []],
                             'Monero': [0, []], 'Gold': [0, []], 'Coal': [0, []], 'Brent': [0, []]}

        self.transactions_history = []
        self.entire_value = 0
        self.entire_value_lst = []

    def buy_asset(self, amount, asset, game):
        amount = int(amount * 10)
        if float(self.cash) >= (game.get_asset_price(asset, game.current_day) / 10 * amount):
            self.asset_amounts[asset.name][0] += amount
            self.cash = self.cash - game.get_asset_price(asset, game.current_day) / 10 * amount
            if amount != 0:
                self.transactions_history.append(f'{game.current_day} BUY {amount / 10} {asset.name} at price {game.get_asset_price(asset, game.current_day)} USD, for {round(game.get_asset_price(asset, game.current_day) * amount / 10, 2)} USD')
            self.asset_amounts[asset.name][1].append(game.get_asset_price(asset, game.current_day) / 10 * amount)

    def sell_asset(self, amount, asset, game):
        amount = int(amount * 10)
        if self.asset_amounts[asset.name][0] >= amount:
            self.asset_amounts[asset.name][0] -= amount
            self.cash = self.cash + game.get_asset_price(asset, game.current_day) / 10 * amount
            if amount != 0:
                self.transactions_history.append(f'{game.current_day} SELL {amount / 10} {asset.name} at price {game.get_asset_price(asset, game.current_day)} USD, for {round(game.get_asset_price(asset, game.current_day) * amount / 10, 2)} USD')
            if self.asset_amounts[asset.name][0] == 0:
                self.asset_amounts[asset.name][1].clear()

    def entire_portfolio_value(self, game):
        self.entire_value = self.cash
        for asset, amount in self.asset_amounts.items():
            try:
                self.entire_value += (game.get_asset_price(globals()[asset.lower()], game.current_day) * amount[0] / 10)
            except KeyError:
                if game.day == 0 or game.day == 1:
                    break
                try:
                    self.entire_value += (game.get_asset_price(globals()[asset.lower()], game.date_list[game.day - 1]) * amount[0] / 10)
                except IndexError:
                    break
                except KeyError:
                    try:
                        self.entire_value += (game.get_asset_price(globals()[asset.lower()], game.date_list[game.day - 2]) * amount[0] / 10)
                    except KeyError:
                        try:
                            self.entire_value += (
                                    game.get_asset_price(globals()[asset.lower()], game.date_list[game.day - 3]) *
                                    amount[0] / 10)
                        except KeyError:
                            self.entire_value += (
                                    game.get_asset_price(globals()[asset.lower()], game.date_list[game.day - 4]) *
                                    amount[0] / 10)

        self.entire_value_lst.append(self.entire_value)
        return self.entire_value


    def encode(self):
        return json.dumps(self.__dict__)

microsoft = Asset('Microsoft', msft_history)
apple = Asset('Apple', apple_history)
tesla = Asset('Tesla', tesla_history)
bitcoin = Asset('Bitcoin', btc_history)
ethereum = Asset('Ethereum', eth_history)
monero = Asset('Monero', xmr_history)
gold = Asset('Gold', gold_history)
coal = Asset('Coal', coal_history)
brent = Asset('Brent', brent_history)

assets_list = [microsoft, apple, tesla, bitcoin, ethereum, monero, gold, coal, brent]
