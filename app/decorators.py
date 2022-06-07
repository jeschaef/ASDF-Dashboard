import logging
from functools import wraps

from flask import url_for, redirect
from flask_login import current_user

log = logging.getLogger()


def confirmation_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        log.debug(f"{current_user} is confirmed? {current_user.confirmed}")
        if not current_user.confirmed:
            return redirect(url_for('auth.unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function
