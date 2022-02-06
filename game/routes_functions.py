from flask import request, session
import plotly
import plotly.express as px
from game.game import *
from game.forms import ActionForm
import json
import pandas as pd


def generate_chart(date_lst: list, entire_values_lst: list) -> str:
    """
    Generate chart from two lists.
        Parameters:
            date_lst (list): List of dates since starting day to current day.
            entire_values_lst (list): List of portfolio values for every day since start day to current day.
        Returns:
            value_graph (str): String represents chart in json format.
    """
    df = pd.DataFrame(dict(Date=date_lst, Value=entire_values_lst))
    fig = px.line(
        df, x="Date", y="Value", title="Entire value chart", width=450, height=250
    )
    fig.update_layout(
        {
            "plot_bgcolor": "rgba(169, 169, 169, 1)",
            "paper_bgcolor": "rgba(169, 169, 169, 1)",
        }
    )
    value_graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return value_graph


def get_zipped_form_list(game: Game) -> tuple:
    """
    Takes Game class instance and returns tuple with form fields
    zipped with available assets dictionary(name:price) and only that dictionary.
        Parameters:
              game (Game): Instance of Game class represents current game state.
        Returns:
             zipped, assets_dict (tuple): tuple with zipped and assets_dict variables
    """
    assets_dict = {}
    forms = []
    for asset in assets_list:
        try:
            assets_dict[asset.name] = game.get_asset_price(asset, game.current_day)
            form = ActionForm(request.form, prefix=asset.name)
            forms.append(form)
        except KeyError:
            continue
    zipped = zip(assets_dict, forms)
    return zipped, assets_dict


def check_user_action(game: Game, portfolio: Portfolio) -> str:
    """
    Takes Game class instance and Portfolio class instance and returns
    string with error if any occurs or empty string if not.
        Parameters:
            game (Game):  Instance of Game class represents current game state.
            portfolio (Portfolio): Instance of Portfolio class represents current portfolio state.
        Returns:
             error (str): String with error message.
    """
    amount = 0
    error = ''
    for i, j in enumerate(request.args):
        if i == 0:
            try:
                amount = float(request.args.get(j))
            except ValueError:
                error = "You have to insert number!"
        elif i == 1:
            if j.split("-")[1] == "buy":
                portfolio.buy_asset(amount, globals()[j.split("-")[0].lower()], game)
                if portfolio.cash < amount * game.get_asset_price(
                    globals()[j.split("-")[0].lower()], game.current_day
                ):
                    error = "Not enough cash!"
            elif j.split("-")[1] == "sell":
                if portfolio.asset_amounts[j.split("-")[0]][0] / 10 < amount:
                    asset = j.split("-")[0]
                    error = f"Not enough {asset}!"
                portfolio.sell_asset(amount, globals()[j.split("-")[0].lower()], game)
            elif j.split("-")[1] == "buyall":
                amount = round(
                    portfolio.cash
                    / game.get_asset_price(
                        globals()[j.split("-")[0].lower()], game.current_day
                    )
                    - 0.05,
                    1,
                )
                portfolio.buy_asset(amount, globals()[j.split("-")[0].lower()], game)
                error = ""
            elif j.split("-")[1] == "sellall":
                amount = portfolio.asset_amounts[j.split("-")[0]][0] / 10
                portfolio.sell_asset(amount, globals()[j.split("-")[0].lower()], game)
                error = ""
    return error


def skip_days(game: Game, portfolio: Portfolio) -> None:
    """
    Takes Game class instance and Portfolio class instance and checks how many days user decide to skip.
        Parameters:
            game (Game):  Instance of Game class represents current game state.
            portfolio (Portfolio): Instance of Portfolio class represents current portfolio state.
    """
    entire_values_lst = session["entire_values_lst"]
    date_lst = session["date_lst"]
    # Go to next day
    if request.form["action"] == "Next Day":
        entire_values_lst.append(portfolio.entire_portfolio_value(game))
        date_lst.append(game.current_day)
        game.next_day()
    # Skip 7 days
    elif request.form["action"] == "Skip 7 Days":
        if len(game.date_list) - game.day >= 7:
            for i in range(7):
                entire_values_lst.append(portfolio.entire_portfolio_value(game))
                date_lst.append(game.current_day)
                game.next_day()
        else:
            for i in range(len(game.date_list) - game.day):
                entire_values_lst.append(portfolio.entire_portfolio_value(game))
                date_lst.append(game.current_day)
                game.next_day()
    # Skip a month
    elif request.form["action"] == "Skip 30 Days":
        if len(game.date_list) - game.day >= 30:
            for i in range(30):
                entire_values_lst.append(portfolio.entire_portfolio_value(game))
                date_lst.append(game.current_day)
                game.next_day()
        else:
            for i in range(len(game.date_list) - game.day):
                entire_values_lst.append(portfolio.entire_portfolio_value(game))
                date_lst.append(game.current_day)
                game.next_day()
