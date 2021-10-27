from wtforms import Form, FloatField, SubmitField
from wtforms.widgets import html5 as h5widgets

class ActionForm(Form):
    amount = FloatField('amount', widget=h5widgets.NumberInput(min=0, step=0.1))
    buy = SubmitField('Buy')
    sell = SubmitField('Sell')
