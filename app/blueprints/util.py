import logging
import math
import os
from urllib.parse import urlparse, urljoin

import pandas as pd
from flask import request, abort, url_for, current_app
from pyclustering.cluster.center_initializer import kmeans_plusplus_initializer
from pyclustering.cluster.xmeans import xmeans
from sklearn.cluster import *

from app.cache import cache
from app.db import db
from app.model import Dataset
from subgroup_detection.util import prepare

log = logging.getLogger()

MAX_QUOTA_MB = int(os.getenv("MAX_QUOTA_MB", 10))

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
    file_path = _get_file_path(owner, dataset)
    log.debug(f"Loading data from file {file_path}")
    with open(file_path, 'r') as f:
        f.seek(0)  # reset buffer to avoid EmptyDataError
        log.debug(f)
        return pd.read_csv(f)


@cache.memoize(60)
def data_size(owner, dataset):
    file_path = _get_file_path(owner, dataset)
    return os.path.getsize(file_path)


def get_user_quota(owner, MAX_QUOTA_MB=MAX_QUOTA_MB):
    all_datasets = Dataset.query.filter_by(owner=owner).all()
    quota_used = {}
    bytes_used = 0
    for d in all_datasets:
        size = data_size(owner, d.id)
        quota_used[d.name] = size
        bytes_used += size
    bytes_free = MAX_QUOTA_MB * 1024 * 1024 - bytes_used
    return {'quota_used': quota_used, 'quota_free': bytes_free}


def delete_data(owner, dataset):
    # Remove selected datasets from database &
    log.debug(f"Delete dataset {dataset}...")
    db.session.delete(dataset)
    db.session.commit()

    # Delete cache entry (if exists)
    cache.delete_memoized(load_data, owner, dataset.id)

    # Remove data files from disk
    file_path = _get_file_path(owner, dataset.id)
    os.remove(file_path)
    log.debug(f"Deleted dataset!")


def delete_all_datasets(owner):
    # Get all the users datasets
    all_datasets = Dataset.query.filter_by(owner=owner).all()
    for d in all_datasets:
        delete_data(owner, d)
    log.debug(f"Deleted all datasets")


def delete_user_account(user):
    # Delete user datasets first
    delete_all_datasets(user.id)

    # Delete user upload folder
    user_folder = _get_user_folder(user.id)
    if os.path.exists(user_folder):
        os.rmdir(user_folder)

    # Delete user account
    db.session.delete(user)
    db.session.commit()
    log.debug(f"Deleted account {user}")


def _get_user_folder(owner):
    return os.path.join(current_app.config['UPLOAD_FOLDER'], owner)


def _get_file_path(owner, dataset):
    user_folder = _get_user_folder(owner)
    return os.path.join(user_folder, dataset + '.csv')


# @cache.memoize(timeout=600)
def get_clustering_info():
    return _model_params()


def _model_dict():
    return {
        "kmeans": KMeans,
        "dbscan": DBSCAN,
        "optics": OPTICS,
        "agglomerative": AgglomerativeClustering,
        "birch": Birch,
        "meanshift": MeanShift,
        "spectral": SpectralClustering
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
        "agglomerative": {
            "n_clusters": "int",
            "affinity": ["euclidean", "l1", "l2", "manhattan", "cosine"],
            "linkage": ["ward", "complete", "average", "single"],
            "distance_threshold": "float",
        },
        "birch": {
            "threshold": "float",
            "branching_factor": "int",
            "n_clusters": "int"
        },
        "meanshift": {
            "bandwidth": "float",
            "bin_seeding": "bool",
            "min_bin_freq": "int",
            "cluster_all": "bool",
            "max_iter": "int"
        },
        "spectral": {
            "n_clusters": "int",
            "n_components": "int",
            "random_state": "int",
            "n_init": "int",
            "gamma": "float",
            "affinity": ["nearest_neighbors", "rbf", "additive_chi2", "chi2", "linear", "poly", "polynomial",
                         "laplacian", "sigmoid", "cosine"],
            "n_neighbors": "int",
            "eigen_tol": "float",
            "assign_labels": ["kmeans", "discretize", "cluster_qr"],
            "degree": "float",
            "coef0": "float",
        }
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
    # return clustering.choose_model(model_cls, param_dict)
    return model_cls().set_params(**param_dict)


def get_param_dict(algorithm, parameters, values):
    if not parameters and not values:  # If lists are empty, return None
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


def estimate_n_clusters(data, categ_columns=None, label_column='class', prediction_column='out'):
    amount_initial_centers = 2
    x = prepare(data, categ_columns=categ_columns, label_column=label_column, prediction_column=prediction_column)
    initial_centers = kmeans_plusplus_initializer(x, amount_initial_centers).initialize()

    kmax = math.floor(math.sqrt(len(data) / 2))
    xmeans_instance = xmeans(x, initial_centers, kmax=kmax)
    xmeans_instance.process()
    return len(xmeans_instance.get_centers())

