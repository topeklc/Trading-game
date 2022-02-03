from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField, StringField, BooleanField, PasswordField, validators, ValidationError
from wtforms.widgets import html5 as h5widgets
from game.models import User
from flask import flash

class ActionForm(FlaskForm):
    amount = FloatField('amount', widget=h5widgets.NumberInput(min=0, step=0.1))
    buy = SubmitField('Buy')
    sell = SubmitField('Sell')
    buyall = SubmitField('Buy with all')
    sellall = SubmitField('Sell everything')


class RegistrationForm(FlaskForm):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=3, max=35)])
    password = PasswordField('New Password', [validators.DataRequired(), validators.Length(min=6, max=35)])
    confirm = PasswordField('Repeat Password', [validators.DataRequired(),
                                                validators.EqualTo('confirm', message='Password must match')])
    accept_policy = BooleanField('Privacy policy')
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. PLease choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. PLease choose a different one.')

    def validate_accept_policy(self, accept_policy):
        if not accept_policy:
            raise ValidationError("You have to accept policy!")

    # def validate_password(self, password):
    #     if password != self.confirm:
    #         raise ValidationError("Password must match!")


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', validators=[validators.DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


def signup_validation(form):
    if User.query.filter_by(email=form.email.data).first():
        flash('User with this email exist!')
    if User.query.filter_by(username=form.username.data).first():
        flash('User with this username exist!')
    if not form.accept_policy.data:
        flash('You have to accept privacy policy!')
    if form.password.data != form.confirm.data:
        flash('Password must match!')
    if len(form.password.data) < 6:
        flash('Password must have at least 6 characters!')
    if len(form.password.data) > 35:
        flash('Password must have less than 35 characters!')
    if len(form.username.data) < 4:
        flash('Username must have at least 4 characters!')
    if len(form.username.data) > 25:
        flash('Username must have less than 25 characters!')
    if len(form.email.data) < 3:
        flash('Email address must have at least 3 characters!')
    if len(form.email.data) > 35:
        flash('Email address must have less than 35 characters!')