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

    def get_asset_price(self, asset):
        price = float("%.2f" % asset.history.loc[self.current_day]['Close'])
        return price

    def next_day(self):
        if self.current_day != self.date_list[-1]:
            self.day += 1
            self.current_day = self.date_list[self.day]
            self.current_weekday = datetime.datetime.strptime(self.current_day, '%Y-%m-%d').strftime('%A')
        else:
            'Game Over'

    def encode(self):
        return json.dumps(self.__dict__)





class Asset:

    def __init__(self, name, history):
        self.name = name
        self.history = history


class Portfolio:

    def __init__(self, start_cash):
        self.cash = float(start_cash)
        self.asset_amounts = {'Microsoft': 0, 'Apple': 0, 'Tesla': 0, 'Bitcoin': 0, 'Ethereum': 0,
                              'Monero': 0, 'Gold': 0, 'Coal': 0, 'Brent': 0}

    def buy_asset(self, amount, asset, game):
        amount = int(amount * 10)
        if float(self.cash) >= (game.get_asset_price(asset) / 10 * amount):
            self.asset_amounts[asset.name] += amount
            self.cash = self.cash - game.get_asset_price(asset) / 10 * amount

    def sell_asset(self, amount, asset, game):
        amount = int(amount * 10)
        if self.asset_amounts[asset.name] >= amount:
            self.asset_amounts[asset.name] -= amount
            self.cash = self.cash + game.get_asset_price(asset) / 10 * amount



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
# for i in assets_list:
#     print("'"+i.name+"'"+':, ', end='')


# game = Game(2017)
# portfolio = Portfolio(100000)
#
#
#
#
#
#
#
# game.next_day()
# game.next_day()
# game.next_day()
# print(game.current_day)
# portfolio.buy_asset(1, bitcoin, game)
# portfolio.buy_asset(50, ethereum, game)
# portfolio.buy_asset(100, tesla, game)
# print(game.get_asset_price(bitcoin))
# print(portfolio.asset_amounts)
# print(portfolio.cash)
# game.next_day()
# game.next_day()
# portfolio.sell_asset(1, bitcoin, game)
# print(portfolio.cash)
# print(portfolio.asset_amounts)
# print(game.current_weekday)