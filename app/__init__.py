import logging
import logging.config
import os

from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from app.login import login_mngr
from app.mail import mail
from app.db import db

from app.blueprints.main import main as main_blueprint
from app.blueprints.auth import auth as auth_blueprint

# Debug toolbar
from app.navigation import nav

toolbar = DebugToolbarExtension()


def create_app(test_config=None):
    # filenames for loading the config are assumed to be relative to the instance path
    # instead of the application root
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',  # TODO setup appropriately
        # DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'test.sqlite'),
        TESTING=True
    )

    # Configure logging
    # log_conf_path = str((get_project_root() / "conf") / "logging.conf")
    # log_file_path = str((get_project_root() / "log") / "demo.log")
    log_conf_path = "conf/logging.conf"
    log_file_path = "log/app.log"

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

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # init extensions
    db.init_app(app)
    toolbar.init_app(app)
    login_mngr.init_app(app)
    mail.init_app(app)
    nav.init_app(app)
    log.debug('Initialized flask extensions')

    # register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app


if __name__ == '__main__':
    app = create_app()
    db.create_all(app=app)  # create db
    app.logger.debug("Created db")
    app.run()
