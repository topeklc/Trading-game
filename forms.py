from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField, StringField, BooleanField, PasswordField, validators, ValidationError
from wtforms.widgets import html5 as h5widgets
from models import User


class ActionForm(FlaskForm):
    amount = FloatField('amount', widget=h5widgets.NumberInput(min=0, step=0.1))
    buy = SubmitField('Buy')
    sell = SubmitField('Sell')
    buyall = SubmitField('Buy with all')
    sellall = SubmitField('Sell everything')


class RegistrationForm(FlaskForm):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [validators.DataRequired()])
    confirm = PasswordField('Repeat Password', [validators.DataRequired(),
                                                validators.EqualTo('confirm', message='Password must match')])
    accept_policy = BooleanField('I accept Privacy policy!')
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. PLease choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. PLease choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')