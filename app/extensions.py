from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = MongoEngine()
login_manager = LoginManager()
mail = Mail()

# Rate limiter - uses IP address as key
# Default: 200 requests per day, 50 per hour for all routes
# Storage: in-memory (use Redis in production for multi-worker)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
