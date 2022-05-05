from celery import Celery
from app.config import Config

celery_app = Celery('__init__')

# Optional configuration, see the application user guide.
celery_app.config_from_object(Config, namespace="CELERY")
celery_app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    celery_app.start()
