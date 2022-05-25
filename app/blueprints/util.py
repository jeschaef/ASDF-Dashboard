import logging
import os
from urllib.parse import urlparse, urljoin

import pandas as pd
from flask import request, abort, url_for, current_app
from sklearn.cluster import *

from app.cache import cache
from subgroup_detection import clustering

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


@cache.memoize(60)  # cache for 1 min TODO change timeout?
def load_data(owner, dataset):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], owner, dataset + '.csv')
    log.debug(f"Loading data from file {file_path}")
    with open(file_path, 'r') as f:
        f.seek(0)  # reset buffer to avoid EmptyDataError
        log.debug(f)
        return pd.read_csv(f)


def delete_data(owner, dataset):
    cache.delete_memoized(load_data, owner, dataset)  # delete from cache, too
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], owner, dataset + '.csv')
    os.remove(file_path)


@cache.memoize(timeout=0)
def get_clustering_info():
    return _model_params()


def _model_dict():
    return {
        "kmeans": KMeans,
        "dbscan": DBSCAN,
        "optics": OPTICS,
    }


def _model_params():
    return {
        "kmeans": {
            "n_clusters": "int",
            "init": ["k-means++", "random"],
            "n_init": "int",
            "max_iter": "int",
            "tol": "float",
            "random_state": "int",
            "algorithm": ["lloyd", "elkan", "auto", "full"]
        },
        "dbscan": {
            "eps": "float",
            "min_samples": "int",
            "metric": _metrics(),
            "metric_params": "dict",
            "algorithm": ["auto", "ball_tree", "kd_tree", "brute"],
            "leaf_size": "int",
            "p": "float"
        },
        "optics": {
            "min_samples": "float",  # or "int"
            "max_eps": "float",
            "metric": _metrics(),
            "metric_params": "dict",
            "p": "float",
            "cluster_method": ["xi", "dbscan"],
            "eps": "float",
            "xi": "float",
            "predecessor_correction": "bool",
            "min_cluster_size": "float",  # or "int"
            "algorithm": ["auto", "ball_tree", "kd_tree", "brute"],
            "leaf_size": "int",
        },
    }


def _metrics():
    return ["cityblock", "cosine", "euclidean", "l1", "l2", "manhattan", "braycurtis", "canberra",
            "chebyshev", "correlation", "dice", "hamming", "jaccard", "kulsinski", "mahalanobis",
            "minkowski", "rogerstanimoto", "russellrao", "seuclidean", "sokalmichener", "sokalsneath",
            "sqeuclidean", "yule"]


def choose_model(algorithm, param_dict):
    model_cls = _model_dict()[algorithm]  # select model from dict
    if param_dict is None:
        param_dict = {}
    return clustering.choose_model(model_cls, param_dict)


def get_param_dict(algorithm, parameters, values):
    if not parameters and not values:       # If lists are empty, return None
        return None

    info = _model_params()[algorithm]
    param_dict = dict(zip(parameters, values))
    for p, v in param_dict.items():
        if info[p] == "int":
            val = int(v)
        elif info[p] == "float":
            val = float(v)
        else:
            val = v
        param_dict[p] = val
    return param_dict
