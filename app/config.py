from os import getenv


class Config:
    SECRET_KEY = 'dev'  # TODO setup appropriate secret & salt
    SALT = 'pepper'
    # SERVER_NAME = '0.0.0.0'

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Caching (may be overwritten by docker-compose file)
    CACHE_REDIS_HOST = getenv('CACHE_REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = getenv('CACHE_REDIS_PORT', 6379)

    # Testing
    # TESTING = True

    # Upload
    ALLOWED_EXTENSIONS = {'csv'}

    # Mail
    MAIL_SERVER = getenv('MAIL_SERVER')
    MAIL_PORT = getenv('MAIL_PORT')
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = True
    MAIL_BACKEND = 'console' #'smtp'
