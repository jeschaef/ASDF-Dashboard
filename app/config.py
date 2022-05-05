class Config:
    SECRET_KEY = 'dev'  # TODO setup appropriate secret
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
