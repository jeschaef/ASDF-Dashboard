import logging
import logging.config
import os

from dotenv import load_dotenv
from flask import Flask

from app.auth import login_mngr
from app.blueprints.auth import auth as auth_blueprint
from app.blueprints.dashboard import dashboard as dashboard_blueprint
from app.blueprints.main import main as main_blueprint
from app.blueprints.task import task as task_blueprint
from app.cache import cache
from app.config import Config
from app.db import db
from app.mail import mail
from app.util import ensure_exists_folder

from app.celery_app import celery_app


def setup_logging(app, app_root):
    log_conf_path = os.path.join(app_root, "conf", "logging.conf")
    log_file_path = os.path.join(app_root, "log", "demo.log")

    logging.config.fileConfig(log_conf_path, defaults={'logfilename': log_file_path})
    return app.logger


def register_extensions(app):
    db.init_app(app)
    # toolbar.init_app(app)
    login_mngr.init_app(app)
    mail.init_app(app)
    cache.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(task_blueprint)


def setup_db(app):
    db.drop_all(app=app)
    db.create_all(app=app)  # create db
    app.logger.debug("Setup db")


def create_app(config):
    # filenames for loading the config are assumed to be relative to the instance path
    # instead of the application root
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'test.sqlite'),
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'upload'),
    )
    app_root = os.path.dirname(app.instance_path)  # App root folder

    # ensure log/instance/upload folders exists
    ensure_exists_folder(os.path.join(app_root, "log"))
    ensure_exists_folder(app.instance_path)
    ensure_exists_folder(app.config['UPLOAD_FOLDER'])

    # Configure logging
    log = setup_logging(app, app_root)
    log.debug('Configured logging')

    # Debug mode
    app.debug = True

    # Register extensions, blueprints
    register_extensions(app)
    log.debug('Registered extensions')

    register_blueprints(app)
    log.debug('Registered blueprints')

    # Setup database
    setup_db(app)

    # Celery
    celery_app.conf.update(app.config)

    return app


if __name__ == '__main__':
    load_dotenv()
    app = create_app(Config)
    app.run()
