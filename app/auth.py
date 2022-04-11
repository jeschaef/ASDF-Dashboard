import logging

import bcrypt
from flask_login import LoginManager

from app.model import User

login_mngr = LoginManager()
log = logging.getLogger()


@login_mngr.user_loader
def load_user(id):
    log.debug(f"Retrieve user with id {id}")
    user = User.query.get(id)
    log.debug(f"Got user {user}")
    return "User"


def get_hashed_password(plain_text_password: str or bytes) -> bytes:
    """
    Hash a password for the first time (using bcrypt, the salt is saved into the hash itself).
    :param plain_text_password: Password in plain text (str or unicode)
    :return: Hashed password
    """
    # Encode if ordinary string
    if isinstance(plain_text_password, str):
        plain_text_password = plain_text_password.encode('utf-8')
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())

def verify_password(plain_text_password: str or bytes, hashed_password: bytes) -> bool:
    """
    Check hashed password.
    :param plain_text_password:
    :param hashed_password:
    :return: True if the passwords match
    """
    #

    # Encode if ordinary string
    if isinstance(plain_text_password, str):
        plain_text_password = plain_text_password.encode('utf-8')
    return bcrypt.checkpw(plain_text_password, hashed_password)
