from flask import Flask, request, render_template, redirect, url_for, session
from main import *
from forms import ActionForm
import secrets
from flask_session import Session
import redis
import pandas as pd
import plotly
import plotly.express as px
import os
from dotenv import load_dotenv
load_dotenv()

redis_url = os.getenv('REDIS_URL')
app = Flask(__name__)
SESSION_TYPE = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(redis_url, ssl_cert_reqs=None)
secret = secrets.token_urlsafe(32)
app.secret_key = secret
app.config.from_object(__name__)
sess = Session(app)



@app.route('/')
def mainpage():
    """Function rendering main page (Settings)."""
    return render_template('main.html')


@app.route('/', methods=['POST', 'GET'])
def start_game():
    """Function starting game with chosen settings."""
    if request.method == 'POST':
        return redirect(url_for('started'))


@app.route('/started', methods=['POST', 'GET'])
def game_start():
    """Function called when user decide to start game.
    Initializing REDIS variables and creating needed objects."""
    starting_cash = request.form['smoney']
    starting_year = request.form['year']
    session['user'] = request.form['user']
    user = session['user']
    game = Game(starting_year)
    session['entire_values_lst'] = []
    session['date_lst'] = []
    entire_values_lst = session['entire_values_lst']
    date_lst = session['date_lst']
    portfolio = Portfolio(starting_cash)
    # Passing game object to cache
    session['game'] = game.encode()
    # Passing portfolio object to cache
    session['portfolio'] = portfolio.encode()
    # Loading game object from Redis cache
    for k, v in json.loads(session['game']).items():
        setattr(game, k, v)
    # Loading portfolio object from Redis cache
    for k, v in json.loads(session['portfolio']).items():
        setattr(portfolio, k, v)
    now = game.current_day
    weekday = game.current_weekday
    portfolio_statement = portfolio.asset_amounts
    entire_value = portfolio.entire_portfolio_value(game)
    assets_dict = {}
    forms = []
    # Creating list of forms for available assets
    for asset in assets_list:
        try:
            assets_dict[asset.name] = game.get_asset_price(asset, game.current_day)
            form = ActionForm(request.form, prefix=asset.name)
            forms.append(form)
        except KeyError:
            print(asset.name)
            pass
    zipped = zip(assets_dict, forms)
    # Chart
    df = pd.DataFrame(dict(
        Date=date_lst,
        Value=entire_values_lst))
    fig = px.line(df, x="Date", y="Value", title="Entire value chart", width=450, height=250)
    value_graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('started_game.html', cash=portfolio.cash,
                           starting_year=starting_year, now=now, zipped=zipped,
                           assets_dict=assets_dict, portfolio=portfolio_statement,
                           weekday=weekday, user=user, entire_value=entire_value, value_graph=value_graph)


@app.route('/day', methods=['POST', 'GET'])
def another_day():
    """Function called when user want to go to another day"""
    game = Game()
    portfolio = Portfolio()
    # Loading game object from Redis cache
    for k, v in json.loads(session['game']).items():
        setattr(game, k, v)
    # Loading portfolio object from Redis cache
    for k, v in json.loads(session['portfolio']).items():
        setattr(portfolio, k, v)
    user = session['user']
    entire_values_lst = session['entire_values_lst']
    date_lst = session['date_lst']
    # Go to next day
    if request.form['action'] == 'Next Day':
        entire_values_lst.append(portfolio.entire_portfolio_value(game))
        date_lst.append(game.current_day)
        game.next_day(1)
    # Skip 7 days
    elif request.form['action'] == 'Skip 7 Days':
        if len(game.date_list) - game.day >= 7:
            for i in range(7):
                entire_values_lst.append(portfolio.entire_portfolio_value(game))
                date_lst.append(game.current_day)
                game.next_day(1)
        else:
            for i in range(len(game.date_list) - game.day):
                entire_values_lst.append(portfolio.entire_portfolio_value(game))
                date_lst.append(game.current_day)
                game.next_day(1)
    # Skip a month
    elif request.form['action'] == 'Skip 30 Days':
        if len(game.date_list) - game.day >= 30:
            for i in range(30):
                entire_values_lst.append(portfolio.entire_portfolio_value(game))
                date_lst.append(game.current_day)
                game.next_day(1)
        else:
            for i in range(len(game.date_list) - game.day):
                entire_values_lst.append(portfolio.entire_portfolio_value(game))
                date_lst.append(game.current_day)
                game.next_day(1)
    # Check if current_day is not last possible day.
    # If it is render score view
    if game.current_day == game.date_list[-1]:
        return scores()
    now = game.current_day
    weekday = game.current_weekday
    assets_dict = {}
    forms = []
    # Creating list of forms for available assets
    for asset in assets_list:
        try:
            assets_dict[asset.name] = game.get_asset_price(asset, game.current_day)
            form = ActionForm(request.form, prefix=asset.name)
            forms.append(form)
        except KeyError:
            pass
    transactions_history = portfolio.transactions_history[-1:-11:-1]
    entire_value = portfolio.entire_portfolio_value(game)
    zipped = zip(assets_dict, forms)
    # Chart
    df = pd.DataFrame(dict(
        Date=date_lst,
        Value=entire_values_lst
    ))
    fig = px.line(df, x="Date", y="Value", title="Entire value chart", width=450, height=250)
    value_graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    # Passing game object to cache
    session['game'] = game.encode()
    # Passing portfolio object to cache
    session['portfolio'] = portfolio.encode()
    return render_template('started_game.html', cash=portfolio.cash, now=now,
                           zipped=zipped, assets_dict=assets_dict, portfolio=portfolio.asset_amounts,
                           weekday=weekday, user=user, transactions_history=transactions_history,
                           entire_value=entire_value, value_graph=value_graph)


@app.route('/up', methods=['POST', 'GET'])
def up_portfolio():
    """Function called when user want to buy or sell asset"""
    game = Game()
    portfolio = Portfolio()
    # Loading game object from Redis cache
    for k, v in json.loads(session['game']).items():
        setattr(game, k, v)
    # Loading portfolio object from Redis cache
    for k, v in json.loads(session['portfolio']).items():
        setattr(portfolio, k, v)
    error = ''
    user = session['user']
    entire_values_lst = session['entire_values_lst']
    date_lst = session['date_lst']
    now = game.current_day
    weekday = game.current_weekday
    amount = 0
    # Loop checking what action user decide to use (buy, sell, buy with all, sell with all,)
    for i, j in enumerate(request.args):
        if i == 0:
            try:
                amount = float(request.args.get(j))
            except ValueError:
                error = 'You have to insert number!'
                pass
        elif i == 1:
            if j.split('-')[1] == 'buy':
                portfolio.buy_asset(amount, globals()[j.split('-')[0].lower()], game)
                if portfolio.cash < amount * game.get_asset_price(globals()[j.split('-')[0].lower()], game.current_day):
                    error = 'Not enough cash!'
            elif j.split('-')[1] == 'sell':
                if portfolio.asset_amounts[j.split('-')[0]][0] / 10 < amount:
                    asset = j.split('-')[0]
                    error = f'Not enough {asset}!'
                portfolio.sell_asset(amount, globals()[j.split('-')[0].lower()], game)
            elif j.split('-')[1] == 'buyall':
                amount = round(portfolio.cash / game.get_asset_price(globals()[j.split('-')[0].lower()], game.current_day) - 0.05, 1)
                portfolio.buy_asset(amount, globals()[j.split('-')[0].lower()], game)
                error = ""
            elif j.split('-')[1] == 'sellall':
                amount = portfolio.asset_amounts[j.split('-')[0]][0] / 10
                portfolio.sell_asset(amount, globals()[j.split('-')[0].lower()], game)
                error = ""
    # Chart
    df = pd.DataFrame(dict(
        Date=date_lst,
        Value=entire_values_lst))
    fig = px.line(df, x="Date", y="Value", title="Entire value chart", width=450, height=250)
    value_graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    assets_dict = {}
    forms = []
    # Creating list of forms for available assets
    for asset in assets_list:
        try:
            assets_dict[asset.name] = game.get_asset_price(asset, game.current_day)
            form = ActionForm(request.form, prefix=asset.name)
            forms.append(form)
        except KeyError:
            pass
    transactions_history = portfolio.transactions_history[-1:-11:-1]
    entire_value = portfolio.entire_portfolio_value(game)
    zipped = zip(assets_dict, forms)
    # Passing game object to cache
    session['game'] = game.encode()
    # Passing portfolio object to cache
    session['portfolio'] = portfolio.encode()
    return render_template('started_game.html', cash=portfolio.cash,
                            now=now, zipped=zipped, assets_dict=assets_dict, portfolio=portfolio.asset_amounts, weekday=weekday, user=user, transactions_history=transactions_history, error=error, entire_value=entire_value, value_graph=value_graph)


@app.route('/stats')
def scores():
    """Function called when current day = last day.
    Rendering score view."""
    game = Game()
    portfolio = Portfolio()
    # Loading game object from Redis cache
    for k, v in json.loads(session['game']).items():
        setattr(game, k, v)
    # Loading portfolio object from Redis cache
    for k, v in json.loads(session['portfolio']).items():
        setattr(portfolio, k, v)
    entire_values_lst = session['entire_values_lst']
    date_lst = session['date_lst']
    entire_value = entire_values_lst[-1]
    roi = (entire_value / portfolio.start_cash * 100) / 100
    # chart of wallet value
    df = pd.DataFrame(dict(
        Date=date_lst,
        Value=entire_values_lst
    ))
    fig = px.line(df, x="Date", y="Value", title="Entire value chart", width=600, height=350)
    value_graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print(entire_values_lst)
    return render_template('stats.html', entire_value=entire_value, roi=roi, value_graph=value_graph)


if __name__ == '__main__':
    app.run()
