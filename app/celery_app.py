import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()
celery_app = Celery('__init__',
                    broker=os.getenv("broker_url", "redis://localhost:6379"),       # specified in docker-compose
                    backend=os.getenv("result_backend", "redis://localhost:6379"))

# Optional configuration
celery_app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    celery_app.start()
