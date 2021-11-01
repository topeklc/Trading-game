from flask import Flask, request, render_template, redirect, url_for, session
from main import *
from forms import ActionForm
import secrets
from flask_session import Session
import redis

app = Flask(__name__)
SESSION_TYPE = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('rediss://:p2e661a327d81ceefd509b9be48dba1219de231ad5652a73110c699ce798dd0a3@ec2-54-77-242-13.eu-west-1.compute.amazonaws.com:11730', ssl_cert_reqs=None)
secret = secrets.token_urlsafe(32)
app.secret_key = secret
app.config.from_object(__name__)
sess = Session(app)



@app.route('/')
def mainpage():
    return render_template('main.html')


@app.route('/', methods=['POST', 'GET'])
def start_game():
    if request.method == 'POST':
        return redirect(url_for('started'))


@app.route('/started', methods=['POST', 'GET'])
def game_start():
    starting_cash = request.form['smoney']
    starting_year = request.form['year']
    session['user'] = request.form['user']
    user = session['user']
    game = Game(starting_year)
    portfolio = Portfolio(starting_cash)
    session['game'] = game.encode()
    session['portfolio'] = portfolio.encode()
    for k, v in json.loads(session['game']).items():
        setattr(game, k, v)
    for k, v in json.loads(session['portfolio']).items():
        setattr(portfolio, k, v)
    now = game.current_day
    weekday = game.current_weekday
    portfolio_statement = portfolio.asset_amounts
    entire_value = portfolio.entire_portfolio_value(game)
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
                           starting_year=starting_year, now=now, zipped=zipped, assets_dict=assets_dict, portfolio=portfolio_statement, weekday=weekday, user=user, entire_value=entire_value)


@app.route('/started', methods=['POST', 'GET'])
def next_day():
    if request.form['action'] == 'Next Day':
        return redirect(url_for('day'))


@app.route('/day', methods=['POST', 'GET'])
def another_day():
    game = Game(2017)
    portfolio = Portfolio(0)
    for k, v in json.loads(session['game']).items():
        setattr(game, k, v)
    for k, v in json.loads(session['portfolio']).items():
        setattr(portfolio, k, v)
    user = session['user']
    game.next_day()
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
            pass
    transactions_history = portfolio.transactions_history[-1:-11:-1]
    entire_value = portfolio.entire_portfolio_value(game)
    zipped = zip(assets_dict, forms)
    session['game'] = game.encode()
    session['portfolio'] = portfolio.encode()
    return render_template('started_game.html', cash=portfolio.cash,
                            now=now, zipped=zipped, assets_dict=assets_dict, portfolio=portfolio.asset_amounts, weekday=weekday, user=user, transactions_history=transactions_history, entire_value=entire_value)


@app.route('/up', methods=['POST', 'GET'])
def up_portfolio():
    game = Game(2017)
    portfolio = Portfolio(0)
    for k, v in json.loads(session['game']).items():
        setattr(game, k, v)
    for k, v in json.loads(session['portfolio']).items():
        setattr(portfolio, k, v)
    error = ''
    user = session['user']
    now = game.current_day
    weekday = game.current_weekday
    amount = 0
    for i, j in enumerate(request.args):
        if i == 0:
            try:
                amount = float(request.args.get(j))
            except ValueError:
                error = 'You have to insert number!'
                break
        if i == 1:
            if j.split('-')[1] == 'buy':
                portfolio.buy_asset(amount, globals()[j.split('-')[0].lower()], game)
                if portfolio.cash < amount * game.get_asset_price(globals()[j.split('-')[0].lower()]):
                    error = 'Not enough cash!'
            elif j.split('-')[1] == 'sell':
                if portfolio.asset_amounts[j.split('-')[0]] /10 < amount:
                    asset = j.split('-')[0]
                    error = f'Not enough {asset}!'
                portfolio.sell_asset(amount, globals()[j.split('-')[0].lower()], game)

    assets_dict = {}
    forms = []
    for asset in assets_list:
        try:
            assets_dict[asset.name] = game.get_asset_price(asset)
            form = ActionForm(request.form, prefix=asset.name)
            forms.append(form)
        except KeyError:
            pass
    transactions_history = portfolio.transactions_history[-1:-11:-1]
    entire_value = portfolio.entire_portfolio_value(game)
    zipped = zip(assets_dict, forms)
    session['game'] = game.encode()
    session['portfolio'] = portfolio.encode()
    return render_template('started_game.html', cash=portfolio.cash,
                            now=now, zipped=zipped, assets_dict=assets_dict, portfolio=portfolio.asset_amounts, weekday=weekday, user=user, transactions_history=transactions_history, error=error, entire_value=entire_value)


if __name__ == '__main__':
    app.run()
