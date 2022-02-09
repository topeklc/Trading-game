from game.game import Game, bitcoin, Portfolio


"""Test Game class functions"""


def test_asset_price():
    """
    GIVEN a Game instance, Asset instance(bitcoin because can be traded also during weekends)
    WHEN Game function asset_price is called
    THEN check every day in given year if returns float
    """
    game = Game(2017)
    for date in game.date_list:
        assert isinstance(game.get_asset_price(bitcoin, date), float)


def test_next_day():
    """
    GIVEN a Game instance
    WHEN Game function next_day is called
    THEN check if game.day increment, if game.current_day equals to 2nd January 2017 and if game.next_day
    is called 370 times game.current_day is 31st December 2017.
    """
    game = Game(2017)
    assert game.day == 0
    game.next_day()
    assert game.day == 1
    assert game.current_day == '2017-01-02'
    for _ in range(370):
        game.next_day()
    assert game.current_day == '2017-12-31'


def test_encode():
    """
    GIVEN a Game instance
    WHEN Game function encode is called
    THEN check if encode returned object is a string.
    """
    game = Game(2017)
    assert isinstance(game.encode(), str)


"""Test Portfolio class functions"""


def test_buy_asset():
    """
    GIVEN a Portfolio instance, Game instance and Asset instance(bitcoin)
    WHEN Portfolio function buy_asset is called
    THEN check if portfolio.cash is lesser than portfolio.start_cash, if portfolio.asset_amounts
    dictionary has changed value and isn't able to buy assets for more than has cash.
    """
    game = Game(2017)
    portfolio = Portfolio(1000)
    portfolio.buy_asset(0.1, bitcoin, game)
    assert portfolio.start_cash > portfolio.cash
    assert portfolio.asset_amounts['Bitcoin'][0] / 10 == 0.1
    price = game.get_asset_price(bitcoin, game.current_day)
    # not exact number but used only for visualize data.
    amount = round(portfolio.asset_amounts['Bitcoin'][1][0] * 10, 2)
    assert amount == price
    cash = portfolio.cash
    portfolio.buy_asset(1000, bitcoin, game)
    assert portfolio.asset_amounts['Bitcoin'][0] != 1000
    assert portfolio.cash == cash


def test_sell_asset():
    """
    GIVEN a Portfolio instance, Game instance and Asset instance(bitcoin)
    WHEN Portfolio function buy_asset is called and then
    Portfolio function sell_asset is called with sam amount
    THEN check if portfolio.cash is equal to portfolio.start_cash, if portfolio.asset_amounts
    dictionary has 0 value and isn't able to sell more assets than has.
    """
    game = Game(2017)
    portfolio = Portfolio(1000)
    portfolio.buy_asset(0.1, bitcoin, game)
    portfolio.sell_asset(0.1, bitcoin, game)
    assert portfolio.cash == portfolio.start_cash
    assert portfolio.asset_amounts['Bitcoin'][0] == 0
    portfolio.sell_asset(100, bitcoin, game)
    assert portfolio.cash == portfolio.start_cash
    assert portfolio.asset_amounts['Bitcoin'][0] == 0
