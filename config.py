import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    MONGODB_SETTINGS = {
        'db': os.environ.get('MONGODB_DB') or 'inventory_db',
        'host': os.environ.get('MONGODB_HOST') or 'localhost',
        'port': int(os.environ.get('MONGODB_PORT') or 27017),
    }
