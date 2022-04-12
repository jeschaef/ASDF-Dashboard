import logging
import logging.config
import os

from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from app.auth import login_mngr
from app.mail import mail
from app.db import db

from app.blueprints.main import main as main_blueprint
from app.blueprints.auth import auth as auth_blueprint
from app.blueprints.dashboard import dashboard as dashboard_blueprint

# Debug toolbar
toolbar = DebugToolbarExtension()


def create_app(test_config=None):
    # filenames for loading the config are assumed to be relative to the instance path
    # instead of the application root
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',  # TODO setup appropriate secret
        # DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'test.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    app_root = os.path.dirname(app.instance_path)  # App root folder

    # ensure log folder exists
    try:
        os.makedirs(os.path.join(app_root, "log"))
    except OSError:
        pass

    # Configure logging
    log_conf_path = os.path.join(app_root, "conf", "logging.conf")
    log_file_path = os.path.join(app_root, "log", "demo.log")

    logging.config.fileConfig(log_conf_path, defaults={'logfilename': log_file_path})
    log = app.logger
    log.debug('Configured logging')

    # Debug mode
    app.debug = True

    if test_config is None:
        # load the instance config, if it exists, when not testing
        # app.config.from_pyfile('config.py', silent=True)
        pass
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists (required for database setup)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # init extensions
    db.init_app(app)
    toolbar.init_app(app)
    login_mngr.init_app(app)
    mail.init_app(app)
    log.debug('Initialized flask extensions')

    # register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(dashboard_blueprint)

    return app


if __name__ == '__main__':
    app = create_app()
    db.drop_all(app=app)
    db.create_all(app=app)  # create db
    app.logger.debug("Created db")
    app.run()
