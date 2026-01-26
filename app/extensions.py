from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_mail import Mail

db = MongoEngine()
login_manager = LoginManager()
mail = Mail()
