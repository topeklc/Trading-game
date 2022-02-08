import yfinance as yf
import pandas as pd
import datetime
import json


"""Getting from yahoo.finance dataframes(price history) for all assets."""


# Stocks
msft_history = yf.Ticker("MSFT").history(start="2016-12-31", end="2022-1-1")
apple_history = yf.Ticker("AAPL").history(start="2016-12-31", end="2022-1-1")
tesla_history = yf.Ticker("TSLA").history(start="2016-12-31", end="2022-1-1")
# Crypto
btc_history = yf.Ticker("BTC-USD").history(start="2016-12-31", end="2022-1-1")
eth_history = yf.Ticker("ETH-USD").history(start="2016-12-31", end="2022-1-1")
xmr_history = yf.Ticker("XMR-USD").history(start="2016-12-31", end="2022-1-1")
# Commodities
gold_history = yf.Ticker("GC=F").history(start="2016-12-31", end="2022-1-1")
coal_history = yf.Ticker("MTF=F").history(start="2016-12-31", end="2022-1-1")
brent_history = yf.Ticker("BZ=F").history(start="2016-12-31", end="2022-1-1")


class Asset:
    def __init__(self, name: str, history) -> None:
        """
        Creates asset instance with name and history dataframe.
        """
        self.name = name
        self.history = history


class Game:
    def __init__(self, year: int = 2017) -> None:
        """
        Initialize Game instance main variables
        """
        self.start = datetime.datetime.strptime(f"{year}-01-01", "%Y-%m-%d").strftime(
            "%d-%m-%Y"
        )
        self.end = datetime.datetime.strptime(f"{year}-12-31", "%Y-%m-%d").strftime(
            "%d-%m-%Y"
        )
        self.date_list = pd.date_range(start=self.start, end=self.end)
        self.date_list = [d.strftime("%Y-%m-%d") for d in self.date_list]
        self.day = 0
        self.current_day = self.date_list[self.day]
        self.current_weekday = datetime.datetime.strptime(
            self.current_day, "%Y-%m-%d"
        ).strftime("%A")

    @staticmethod
    def get_asset_price(asset: Asset, current_day: str) -> float:
        """
        Gets asset price.
            Parameters:
                asset (Asset): Instance of class Asset.
                current_day (str): String represents date in format YYYY-MM-DD.
            Returns:
                price (float): Float number rounded to 2 decimal places.
        """
        price = float("%.2f" % asset.history.loc[current_day]["Close"])
        return price

    def next_day(self) -> None:
        """
        Moves to another day.
        """
        try:
            self.day += 1
            self.current_day = self.date_list[self.day]
            self.current_weekday = datetime.datetime.strptime(
                self.current_day, "%Y-%m-%d"
            ).strftime("%A")
        except IndexError:
            # Trigger when try to move to day that is out of range and set current_day to last day in date_list.
            self.current_day = self.date_list[-1]

    def encode(self) -> str:
        """
        Helps transfer data to Redis.
            Returns:
                encoded_class (str): String represents instance state in json format.
        """
        encoded_class = json.dumps(self.__dict__)
        return encoded_class


class Portfolio:
    def __init__(self, start_cash: int = 0) -> None:
        """Initialize main variables."""
        self.start_cash = float(start_cash)
        self.cash = self.start_cash
        # First item in value list is amount of asset that user own.
        # Second item is a list with values spent to buy asset to calculate average buy price.
        self.asset_amounts = {
            "Microsoft": [0, []],
            "Apple": [0, []],
            "Tesla": [0, []],
            "Bitcoin": [0, []],
            "Ethereum": [0, []],
            "Monero": [0, []],
            "Gold": [0, []],
            "Coal": [0, []],
            "Brent": [0, []],
        }
        # List of strings with user transactions history displayed in portfolio
        self.transactions_history = []
        self.entire_value = 0
        self.entire_value_lst = []

    def buy_asset(self, amount: float, asset: Asset, game: Game) -> None:
        """
        Called when user try to buy asset.
        Checks if user has enough money to buy and update portfolio state.
            Parameters:
                amount (float): Float number represents amount of asset which user wants to buy.
                asset (Asset): Instance of class Asset represents asset which user wants to buy.
                game (Game): Instance of Game class represents current game state.
        """
        amount = int(amount * 10)
        if float(self.cash) >= (
            game.get_asset_price(asset, game.current_day) / 10 * amount
        ):
            self.asset_amounts[asset.name][0] += amount
            self.cash = (
                self.cash - game.get_asset_price(asset, game.current_day) / 10 * amount
            )
            if amount != 0:
                self.transactions_history.append(
                    f"{game.current_day} BUY {amount / 10} {asset.name} at price {game.get_asset_price(asset, game.current_day)} USD, for {round(game.get_asset_price(asset, game.current_day) * amount / 10, 2)} USD"
                )
            self.asset_amounts[asset.name][1].append(
                game.get_asset_price(asset, game.current_day) / 10 * amount
            )

    def sell_asset(self, amount: float, asset: Asset, game: Game) -> None:
        """
        Called when user try to sell asset.
        Checks if user has enough asset to sell and update portfolio state.
            Parameters:
                amount (float): Float represents amount of asset which user wants to sell.
                asset (Asset): Instance of class Asset represents asset which user wants to sell.
                game (Game): Instance of Game class represents current game state.
        """
        amount = int(amount * 10)
        if self.asset_amounts[asset.name][0] >= amount:
            self.asset_amounts[asset.name][0] -= amount
            self.cash = (
                self.cash + game.get_asset_price(asset, game.current_day) / 10 * amount
            )
            if amount != 0:
                self.transactions_history.append(
                    f"{game.current_day} SELL {amount / 10} {asset.name} at price {game.get_asset_price(asset, game.current_day)} USD, for {round(game.get_asset_price(asset, game.current_day) * amount / 10, 2)} USD"
                )
            # Clear list of spent values if no more asset left in portfolio
            if self.asset_amounts[asset.name][0] == 0:
                self.asset_amounts[asset.name][1].clear()

    def entire_portfolio_value(self, game: Game) -> float:
        """
        Calculates whole portfolio value. Since stocks have no price feed at weekends and holidays
        It has to check few previous days to find price of asset for portfolio value calculation.
            Parameters:
                game (Game): Instance of Game class represents current game state.
            Returns:
                self.entire_value (float): Float number represents current user's portfolio value
        """
        self.entire_value = self.cash
        for asset, amount in self.asset_amounts.items():
            try:
                self.entire_value += (
                    game.get_asset_price(globals()[asset.lower()], game.current_day)
                    * amount[0]
                    / 10
                )
            except KeyError:
                for d in range(1, 30):
                    try:
                        # Try to get asset price from day before if not available in current day.
                        self.entire_value += (
                            game.get_asset_price(
                                globals()[asset.lower()], game.date_list[game.day - d]
                            )
                            * amount[0]
                            / 10
                        )
                        break
                    except IndexError:
                        break
                    except KeyError:
                        continue
        self.entire_value_lst.append(self.entire_value)
        return self.entire_value

    def encode(self) -> str:
        """
        Helps transfer data to Redis.
            Returns:
                encoded_class (str): String represents instance state in json format.
        """
        return json.dumps(self.__dict__)


"""
Initialize Asset class instances.
"""
microsoft = Asset("Microsoft", msft_history)
apple = Asset("Apple", apple_history)
tesla = Asset("Tesla", tesla_history)
bitcoin = Asset("Bitcoin", btc_history)
ethereum = Asset("Ethereum", eth_history)
monero = Asset("Monero", xmr_history)
gold = Asset("Gold", gold_history)
coal = Asset("Coal", coal_history)
brent = Asset("Brent", brent_history)
assets_list = [microsoft, apple, tesla, bitcoin, ethereum, monero, gold, coal, brent]
