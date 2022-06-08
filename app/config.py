from os import getenv


class Config:
    SECRET_KEY = 'dev'  # TODO setup appropriate secret & salt
    SALT = 'pepper'
    # DATABASE=os.path.join(app.instance_path, 'app.sqlite')

    # Celery
    CELERY_BROKER_URL = 'redis://localhost:6379'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379'

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Testing
    TESTING = True

    # Upload
    ALLOWED_EXTENSIONS = {'csv'}

    # Mail
    MAIL_SERVER = getenv('MAIL_SERVER')
    MAIL_PORT = getenv('MAIL_PORT')
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = True
    MAIL_BACKEND = 'console' #'smtp'
