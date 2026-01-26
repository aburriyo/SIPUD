import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    MONGODB_SETTINGS = {
        'db': os.environ.get('MONGODB_DB') or 'inventory_db',
        'host': os.environ.get('MONGODB_HOST') or 'localhost',
        'port': int(os.environ.get('MONGODB_PORT') or 27017),
    }

    # Sesiones - Cookie "Recordarme" dura 30 días
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Email (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Token de reset expira en 1 hora
    PASSWORD_RESET_TOKEN_MAX_AGE = 3600
