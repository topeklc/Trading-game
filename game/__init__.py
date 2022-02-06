from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import secrets
from flask_session import Session
import redis
import os
from dotenv import load_dotenv

load_dotenv()
redis_url = os.getenv("REDISTOGO_URL")
app = Flask(__name__)
db_url = os.getenv("DATABASE_URL")
secret_db = secrets.token_urlsafe(32)
SESSION_TYPE = "redis"
app.config["SESSION_REDIS"] = redis.from_url(redis_url)
app.config["SECRET_KEY"] = secret_db
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
secret = secrets.token_urlsafe(32)
app.secret_key = secret
app.config.from_object(__name__)
sess = Session(app)


from game.routes import *
