from flask import request, render_template, redirect, url_for, session, flash
from flask_login import login_user, current_user, logout_user
import plotly
import plotly.express as px
from game.forms import *
from game.models import *
from game import app, bcrypt, db
from game.main import *

login_manager.init_app(app)

@app.route('/')
def mainpage():
    """
    Function rendering main page.
    """
    return render_template('index.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    """
    Function pass data to database and rendering sign up page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('settings'))
    form = RegistrationForm()
    if form.validate_on_submit():
        print(form.accept_policy.data)
        hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pwd, best_score=0)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    if form.email.data or form.username.data:
        if User.query.filter_by(email=form.email.data).first():
            flash('User with this email exist!')
        elif User.query.filter_by(username=form.username.data).first():
            flash('User with this username exist!')
        elif not form.accept_policy.data:
            flash('You have to accept privacy policy')
        elif form.password.data != form.confirm.data:
            flash('Passwords must match!')
    return render_template('signup.html', form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    Function check if login data provided
    by user exist in database and rendering login page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('settings'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Login successful.')
            return redirect('/')
        else:
            flash('Login Unsuccessful.')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You are logged out!')
    return redirect('/')


@app.route('/settings', methods=['POST', 'GET'])
def settings():
    """
    Function render settings page.
    """
    return render_template('settings.html')

@app.route('/settings', methods=['POST', 'GET'])
def start_game():
    """
    Function starting game with chosen settings.
    """
    if request.method == 'POST':
        return redirect(url_for('started'))


@app.route('/started', methods=['POST', 'GET'])
def game_start():
    """
    Function called when user decide to start game.
    Initializing REDIS variables and creating needed objects.
    """
    starting_cash = request.form['smoney']
    starting_year = request.form['year']
    if current_user.is_authenticated:
        session['user'] = current_user.username
    else:
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
    """
    Function called when user want to go to another day
    """
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
    """
    Function called when user want to buy or sell asset
    """
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
    """
    Function called when current day = last day.
    Rendering score view and if it's the best score add it to database.
    """
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
    roi = (entire_value - portfolio.start_cash) / portfolio.start_cash * 100
    if current_user.is_authenticated:
        if roi > int(current_user.best_score):
            current_user.best_score = int(roi)
            db.session.merge(current_user)
            db.session.commit()
            flash("It's your best score!")
        else:
            flash(f"That's not your best score. Your best score is {current_user.best_score} %")

    # chart of wallet value
    df = pd.DataFrame(dict(
        Date=date_lst,
        Value=entire_values_lst
    ))
    fig = px.line(df, x="Date", y="Value", title="Entire value chart", width=600, height=350)
    value_graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print(entire_values_lst)
    return render_template('stats.html', entire_value=entire_value, roi=roi, value_graph=value_graph)


