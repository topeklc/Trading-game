from flask import Flask, request, render_template, redirect, url_for
from game import *
from forms import ActionForm

app = Flask(__name__)

portfolio = Portfolio(0)
game = Game(2017)


@app.route('/')
def mainpage():
    return render_template('main.html')


@app.route('/', methods=['POST', 'GET'])
def start_game():
    if request.method == 'POST':
        return redirect(url_for('game'))


@app.route('/game', methods=['POST', 'GET'])
def game():
    global portfolio
    starting_cash = request.form['smoney']
    starting_year = request.form['year']
    game = Game(starting_year)
    portfolio = Portfolio(starting_cash)
    now = game.current_day
    weekday = game.current_weekday
    assets_dict = {}
    forms = []
    for asset in assets_list:
        try:
            assets_dict[asset.name] = game.get_asset_price(asset)
            form = ActionForm(request.form, prefix=asset.name)
            forms.append(form)
        except KeyError:
            print(asset.name)
            pass
    print(assets_dict)
    zipped = zip(assets_dict, forms)
    return render_template('started_game.html', cash=portfolio.cash,
                           starting_year=starting_year, now=now, zipped=zipped, assets_dict=assets_dict, weekday=weekday)


@app.route('/game', methods=['POST', 'GET'])
def next_day():
    if request.form['action'] == 'Next Day':
        return redirect(url_for('another_day'))


@app.route('/another_day', methods=['POST', 'GET'])
def another_day():
    global game
    game.next_day()
    portfolioo = portfolio
    now = game.current_day
    weekday = game.current_weekday
    portfolio_statement = portfolioo.asset_amounts
    assets_dict = {}
    forms = []
    for asset in assets_list:
        try:
            assets_dict[asset.name] = game.get_asset_price(asset)
            form = ActionForm(request.form, prefix=asset.name)
            forms.append(form)
        except KeyError:
            pass
    zipped = zip(assets_dict, forms)
    return render_template('started_game.html', cash=portfolioo.cash,
                            now=now, zipped=zipped, assets_dict=assets_dict, portfolio=portfolio_statement, weekday=weekday)


@app.route('/up_portfolio', methods=['POST', 'GET'])
def up_portfolio():
    global game
    portfolioo = portfolio
    now = game.current_day
    weekday = game.current_weekday
    portfolio_statement = portfolioo.asset_amounts
    amount = 0
    for i, j in enumerate(request.args):
        if i == 0:
            amount = float(request.args.get(j))
        if i == 1:
            if j.split('-')[1] == 'buy':
                portfolioo.buy_asset(amount, globals()[j.split('-')[0].lower()], game)
            elif j.split('-')[1] == 'sell':
                portfolioo.sell_asset(amount, globals()[j.split('-')[0].lower()], game)

    assets_dict = {}
    forms = []
    for asset in assets_list:
        try:
            assets_dict[asset.name] = game.get_asset_price(asset)
            form = ActionForm(request.form, prefix=asset.name)
            forms.append(form)
        except KeyError:
            pass
    zipped = zip(assets_dict, forms)
    return render_template('started_game.html', cash=portfolioo.cash,
                            now=now, zipped=zipped, assets_dict=assets_dict, portfolio=portfolio_statement, weekday=weekday)


if __name__ == '__main__':
    app.run(debug=True)
