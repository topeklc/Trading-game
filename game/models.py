from game.__init__ import db, app, bcrypt
from flask_login import UserMixin, LoginManager


login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    best_score = db.Column(db.Integer)

    def __init__(self, username: str, email: str, password: str, best_score: int = 0):
        self.username = username
        self.email = email
        self.hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.best_score = best_score

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
