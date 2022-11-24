from os import getenv

class BaseConfig:
    TESTING = False
    DEBUG = False
    SECRET_KEY = 'dev'
    SALT = 'pepper'
    # SERVER_NAME = getenv('SERVER_NAME', '127.0.0.1:5000')

    # Upload
    ALLOWED_EXTENSIONS = {'csv'}

    # Mail
    MAIL_SERVER = getenv('MAIL_SERVER')
    MAIL_PORT = getenv('MAIL_PORT')
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = True

    # Caching (may be overwritten by docker-compose file)
    CACHE_REDIS_HOST = getenv('CACHE_REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = getenv('CACHE_REDIS_PORT', 6379)

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevConfig(BaseConfig):
    FLASK_ENV = 'development'
    DEBUG = True
    MAIL_BACKEND = 'console'
    APP_URL_PREFIX = '/asdf'    # set to '' or comment out for dev deployment without prefix


class ProductionConfig(BaseConfig):
    FLASK_ENV = 'production'
    MAIL_BACKEND = 'smtp'
    APPLICATION_ROOT = 'asdf'   # set your application root here if necessary
