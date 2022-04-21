import logging
import os
from urllib.parse import urlparse, urljoin

import pandas as pd
from flask import request, abort, url_for, current_app

from app.cache import cache

log = logging.getLogger()


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


def redirect_url(endpoint='main.index'):
    next = request.args.get('next')
    if not is_safe_url(next):
        return abort(400)
    return next or url_for(endpoint)


@cache.memoize(60)      # cache for 1 min
def load_data(owner, dataset):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], owner, dataset + '.csv')
    log.debug(f"Loading data from file {file_path}")
    return pd.read_csv(file_path)
