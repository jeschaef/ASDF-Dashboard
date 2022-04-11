import logging

import bcrypt
from flask_login import LoginManager

login_mngr = LoginManager()
log = logging.getLogger()


@login_mngr.user_loader
def load_user(id):
    log.debug(f"Retrieve user with id {id}")
    return "User"


def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())

def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)
