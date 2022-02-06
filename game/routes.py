from flask import render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from game.forms import (
    RegistrationForm,
    LoginForm,
    signup_validation,
    login_validation,
)
from game.models import login_manager, User
from game import app, bcrypt, db
from game.routes_functions import *

login_manager.init_app(app)


@app.route("/")
def mainpage():
    """
    Renders main page.
    """
    return render_template("index.html")


@app.route("/signup", methods=["POST", "GET"])
def signup():
    """
    Passes data to database and rendering sign up page.
    """
    if current_user.is_authenticated:
        return redirect(url_for("settings"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pwd = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_pwd,
            best_score=0,
        )
        db.session.add(user)
        db.session.commit()
        flash("Your account has been created! You are now able to log in", "success")
        return redirect(url_for("login"))
    if form.email.data or form.username.data:
        # getting flash message/s if something went wrong.
        signup_validation(form)

    return render_template("signup.html", form=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    """
    Checks if login data provided
    by user exist in database and rendering login page.
    """
    if current_user.is_authenticated:
        return redirect(url_for("settings"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Login successful.")
            return redirect("/")
        else:
            login_validation(user, form)
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash("You are logged out!")
    return redirect("/")


@app.route("/settings", methods=["POST", "GET"])
def settings():
    """
    Renders settings page.
    """
    return render_template("settings.html")


@app.route("/settings", methods=["POST", "GET"])
def start_game():
    """
    Starts game with chosen settings.
    """
    if request.method == "POST":
        return redirect(url_for("started"))


@app.route("/started", methods=["POST", "GET"])
def game_start():
    """
    Called when user decide to start game.
    Initializing REDIS variables and creating needed objects.
    """
    starting_cash = request.form["smoney"]
    starting_year = request.form["year"]
    if current_user.is_authenticated:
        session["user"] = current_user.username
    else:
        session["user"] = request.form["user"]
    user = session["user"]
    game = Game(int(starting_year))
    session["entire_values_lst"] = []
    session["date_lst"] = []
    entire_values_lst = session["entire_values_lst"]
    date_lst = session["date_lst"]
    portfolio = Portfolio(int(starting_cash))
    # Passing game object to cache
    session["game"] = game.encode()
    # Passing portfolio object to cache
    session["portfolio"] = portfolio.encode()
    # Loading game object from Redis cache
    for k, v in json.loads(session["game"]).items():
        setattr(game, k, v)
    # Loading portfolio object from Redis cache
    for k, v in json.loads(session["portfolio"]).items():
        setattr(portfolio, k, v)
    now = game.current_day
    weekday = game.current_weekday
    portfolio_statement = portfolio.asset_amounts
    entire_value = portfolio.entire_portfolio_value(game)
    # Form fields for available assets
    zipped = get_zipped_form_list(game)[0]
    # Dictionary with assets names and prices
    assets_dict = get_zipped_form_list(game)[1]
    # Chart
    value_graph = generate_chart(date_lst, entire_values_lst)
    return render_template(
        "started_game.html",
        cash=portfolio.cash,
        starting_year=starting_year,
        now=now,
        zipped=zipped,
        assets_dict=assets_dict,
        portfolio=portfolio_statement,
        weekday=weekday,
        user=user,
        entire_value=entire_value,
        value_graph=value_graph,
    )


@app.route("/day", methods=["POST", "GET"])
def another_day():
    """
    Called when user want to go to another day
    """
    game = Game()
    portfolio = Portfolio()
    # Loading game object from Redis cache
    for k, v in json.loads(session["game"]).items():
        setattr(game, k, v)
    # Loading portfolio object from Redis cache
    for k, v in json.loads(session["portfolio"]).items():
        setattr(portfolio, k, v)
    user = session["user"]
    entire_values_lst = session["entire_values_lst"]
    date_lst = session["date_lst"]
    # Checking how many days user decide to skip
    skip_days(game, portfolio)
    # Checking if current_day is not last possible day,
    # if is renders score view.
    if game.current_day == game.date_list[-1]:
        return scores()
    now = game.current_day
    weekday = game.current_weekday
    transactions_history = portfolio.transactions_history[-1:-11:-1]
    entire_value = portfolio.entire_portfolio_value(game)
    # Form fields for available assets
    zipped = get_zipped_form_list(game)[0]
    # Dictionary with assets names and prices
    assets_dict = get_zipped_form_list(game)[1]
    # Chart
    value_graph = generate_chart(date_lst, entire_values_lst)
    # Passing game object to cache
    session["game"] = game.encode()
    # Passing portfolio object to cache
    session["portfolio"] = portfolio.encode()
    return render_template(
        "started_game.html",
        cash=portfolio.cash,
        now=now,
        zipped=zipped,
        assets_dict=assets_dict,
        portfolio=portfolio.asset_amounts,
        weekday=weekday,
        user=user,
        transactions_history=transactions_history,
        entire_value=entire_value,
        value_graph=value_graph,
    )


@app.route("/up", methods=["POST", "GET"])
def up_portfolio():
    """
    Called when user want to buy or sell asset
    """
    game = Game()
    portfolio = Portfolio()
    # Loading game object from Redis cache
    for k, v in json.loads(session["game"]).items():
        setattr(game, k, v)
    # Loading portfolio object from Redis cache
    for k, v in json.loads(session["portfolio"]).items():
        setattr(portfolio, k, v)
    user = session["user"]
    entire_values_lst = session["entire_values_lst"]
    date_lst = session["date_lst"]
    now = game.current_day
    weekday = game.current_weekday
    # checks what action user decide to use (buy, sell, buy with all, sell with all,)
    error = check_user_action(game, portfolio)
    # Form fields for available assets
    zipped = get_zipped_form_list(game)[0]
    # Dictionary with assets names and prices
    assets_dict = get_zipped_form_list(game)[1]
    # Chart
    value_graph = generate_chart(date_lst, entire_values_lst)
    transactions_history = portfolio.transactions_history[-1:-11:-1]
    entire_value = portfolio.entire_portfolio_value(game)
    # Passing game object to cache
    session["game"] = game.encode()
    # Passing portfolio object to cache
    session["portfolio"] = portfolio.encode()
    return render_template(
        "started_game.html",
        cash=portfolio.cash,
        now=now,
        zipped=zipped,
        assets_dict=assets_dict,
        portfolio=portfolio.asset_amounts,
        weekday=weekday,
        user=user,
        transactions_history=transactions_history,
        error=error,
        entire_value=entire_value,
        value_graph=value_graph,
    )


@app.route("/stats")
def scores():
    """
    Called when current day = last day.
    Rendering score view and if it's the best score add it to database.
    """
    game = Game()
    portfolio = Portfolio()
    # Loading game object from Redis cache
    for k, v in json.loads(session["game"]).items():
        setattr(game, k, v)
    # Loading portfolio object from Redis cache
    for k, v in json.loads(session["portfolio"]).items():
        setattr(portfolio, k, v)
    entire_values_lst = session["entire_values_lst"]
    date_lst = session["date_lst"]
    entire_value = entire_values_lst[-1]
    roi = (entire_value - portfolio.start_cash) / portfolio.start_cash * 100
    if current_user.is_authenticated:
        if roi > int(current_user.best_score):
            current_user.best_score = int(roi)
            db.session.merge(current_user)
            db.session.commit()
            flash("It's your best score!")
        else:
            flash(
                f"That's not your best score. Your best score is {current_user.best_score} %"
            )
    # chart
    value_graph = generate_chart(date_lst, entire_values_lst)
    # leaderboard
    leaderboard = []
    users = User.query.order_by(User.best_score.desc()).limit(10).all()
    for user in users:
        leaderboard.append((user.username, user.best_score))
    return render_template(
        "stats.html",
        entire_value=entire_value,
        roi=roi,
        value_graph=value_graph,
        leaderboard=leaderboard,
    )
