import json
import logging
import os
import typing
from urllib.parse import urlparse, urljoin

import inspect
from sklearn.cluster import *

import pandas as pd
from flask import request, abort, url_for, current_app

import subgroup_detection.clustering
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


# @cache.memoize(timeout=0)
def get_clustering_info(only_names=True):
    info = {}
    signatures = _inspect_models()
    for name in signatures:
        signature = signatures[name]
        # log.debug(signature)
        # log.debug(signature.parameters)
        params = {}
        for p in signature.parameters.values():
            if p.name == 'self':
                continue
            if only_names:
                params[p.name] = ""
            else:
                params[p.name] = [type(p.default), p.default]
        info[name] = params
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


def _inspect_models():
    return {k: _inspect(m) for k, m in _model_dict().items()}


def _inspect(m):
    return inspect.signature(m.__init__)


def choose_model(algorithm, param_dict):
    model_cls = _model_dict()[algorithm]  # select model from dict
    return clustering.choose_model(model_cls, param_dict)
    # log.info(f"model_cls {model_cls}, param_dict={param_dict}")
    # signature = _inspect(model_cls)
    # log.info(f"Typing {typing.get_type_hints(model_cls.__init__)}")
    # for p_name, val in param_dict.items():
    #     p = signature.parameters[p_name]
    #     log.info(f"Parameter: {p_name}, {p.default}, {type(p.default)}, {p.annotation}")
    #     param_cls = type(p.default)
    #     log.info(f"Class: {param_cls}, {param_cls(val)}, {type(param_cls(val))}")
    #     param_dict[p_name] = param_cls(val)
    # model = model_cls(**param_dict)             # instantiate model object with parameters
    # return model
