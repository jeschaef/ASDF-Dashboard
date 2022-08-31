import logging

import pandas as pd
from lime.lime_tabular import LimeTabularExplainer
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.cluster import KMeans
from sklearn.neighbors import KNeighborsClassifier
from pandas import Series, DataFrame
from shap import KernelExplainer
import numpy as np

log = logging.getLogger()


def validate_clustering(X, labels):
    """
    Compute different cluster validation indices.
    @param X: Numeric data
    @type X: pd.DataFrame or array
    @param labels: Cluster labels
    @type labels: list of int
    @return: Series containing CVI values
    @rtype: Series
    """
    sil = silhouette_score(X, labels)
    dbi = davies_bouldin_score(X, labels)
    chi = calinski_harabasz_score(X, labels)
    return Series(data={'sil': sil, 'dbi': dbi, 'chi': chi})


def explain_clustering_shap(model, data, sample_frac=0.1, min_sample_size=10):
    """
    Explain a given clustering model using SHAP.
    :param model: Clustering model.
    :param data: The numerical dataset used to train the clustering model (preprocessed) without labels.
    :param sample_frac: Fraction of instances of a cluster to sample for explanation of the clustering
    :param min_sample_size: Minimal number of instances (if possible) to sample from a cluster for
        clustering explanation.
    :return: SHAP values for each instance grouped by cluster
    """
    cluster_shap = {}
    labels = model.labels_
    n_clusters = labels.max() + 1

    # Train a kmeans model for KernelExplainer background data
    kmeans = KMeans(n_clusters=n_clusters).fit(data)

    # Iterate over all clusters and explain them (one-vs-all)
    for c in range(0, n_clusters):

        # If the model is able to predict inputs, use this for KernelExplainer
        # Otherwise, train a k-NN model to predict cluster membership
        if can_predict(model):
            f = lambda X: (model.predict(X) == c).astype(int)  # one-vs-all approach (cluster ec vs rest)
        else:
            knn = KNeighborsClassifier(n_neighbors=7, weights='distance').fit(data, labels)
            f = lambda X: (knn.predict(X) == c).astype(int)

        # Sample instances of cluster c
        samples = sample_cluster(data,
                                 labels,
                                 c,
                                 sample_frac=sample_frac,
                                 min_sample_size=min_sample_size)

        # Explain cluster c
        explainer = KernelExplainer(f, DataFrame(kmeans.cluster_centers_, columns=data.columns))
        shap_values = explainer.shap_values(samples)
        cluster_shap[c] = DataFrame(shap_values, columns=data.columns)

    return cluster_shap


def patterns_from_cluster_shap(cluster_shap, data, dataX, labels, shap_threshold=0.1, prefix_sep='#'):
    """
    Extract patterns (rules) from the SHAP explanations of the clustering model.
    :param cluster_shap: SHAP values of each instance grouped by cluster.
    :param data: The original dataset (not preprocessed).
    :param dataX: The numerical dataset used to train the clustering model (preprocessed) without labels.
    :param labels: Clustering labels.
    :param shap_threshold: Minimal mean SHAP value of a feature to be considered for a pattern.
    :return: Set of patterns for each cluster
    """
    cluster_patterns = {}
    for c in cluster_shap:

        # Get SHAP, mean SHAP and data instances of cluster c
        shap_vals = cluster_shap[c]
        mean_shap_vals = shap_vals.mean()
        cdata = data[labels == c]
        cluster_data = DataFrame(dataX.values[labels == c], columns=dataX.columns)

        # For each feature with mean SHAP value above the shap_threshold,
        # extract a pattern of the form 'feature =/!= value'
        patterns = []
        for fn in mean_shap_vals[mean_shap_vals > shap_threshold].keys():

            # Split the feature names according to the prefix_sep used in one-hot-encoding the data
            split = fn.split(prefix_sep, maxsplit=1)
            col = split[0]

            if len(split) == 1:  # not one-hot-encoded feature (not categorical)
                args, _ = np.unique(cdata[col], return_counts=True)
                min_val, max_val = args[0], args[-1]
                min_global, max_global = data[col].min(), data[col].max()

                # Define range constraint
                if min_val == max_val:
                    patterns.append((col, '=', min_val))
                elif min_val == min_global and max_val == max_global:
                    pass   # no pattern added as it would be true for any value
                elif min_val == min_global:
                    patterns.append((col, '<=', max_val))
                elif max_val == max_global:
                    patterns.append((col, '>=', min_val))
                else:
                    patterns.append((col, '>=', min_val))
                    patterns.append((col, '<=', max_val))
            elif len(split) == 2:  # one-hot-encoded feature
                val = pd.Series(data=split[1]).astype(cdata[col].dtype).iloc[0]  # parse split[1] (str) to original type
                argmax = np.bincount(cluster_data[fn]).argmax()     # argmax is 0 or 1 (False or True)

                # If the one-hot-encoded feature is binary and the condition negated (argmax=0),
                # find the counter part (e.g. sex#M==0 --> sex != M --> sex=F).
                if argmax == 0:
                    unq = np.unique(data[col])  # unique values for original column (e.g. sex --> [M, F])
                    if len(unq) == 2:
                        counter_val = unq[0] if unq[1] == val else unq[1]
                        patterns.append((col, '=', counter_val))
                    else:
                        patterns.append((col, '!=', val))
                else:
                    patterns.append((col, '=', val))
        # Store patterns for cluster c
        cluster_patterns[c] = patterns

    return cluster_patterns


def explain_clustering_lime(model, data, sample_frac=0.01, min_sample_size=5, prefix_sep='#'):
    n_feat = len(data.columns)
    labels = model.labels_
    n_clusters = labels.max() + 1
    cat_feat = [i for i, col in enumerate(data.columns) if prefix_sep in col]
    explainer = LimeTabularExplainer(data.values,
                                     feature_names=data.columns,
                                     discretize_continuous=True,
                                     categorical_features=cat_feat)

    cluster_lime = {}
    for c in range(0, n_clusters):
        # Get data of cluster c
        indices = (labels == c).astype(int)
        cdata = pd.DataFrame(data.values[indices.astype(bool)], columns=data.columns)
        samples = sample_cluster(data,
                                 labels,
                                 c,
                                 sample_frac=sample_frac,
                                 min_sample_size=min_sample_size)

        # If the model is able to predict inputs, use this for LimeTabularExplainer
        # Otherwise, train a k-NN model to predict cluster membership
        # Predict probability for class 1 (=[0,1]) or 0 (=[1,0])
        if can_predict(model):
            f = lambda X: np.array([[0, 1] if b else [1, 0] for b in model.predict(X) == c])    # one-vs-rest
        else:
            knn = KNeighborsClassifier(n_neighbors=7, weights='distance').fit(data, labels)
            f = lambda X: np.array([[0, 1] if b else [1, 0] for b in knn.predict(X) == c])

        # Explain sample instances of cluster c
        lime = np.zeros(n_feat)
        exps = []
        for _, row in samples.iterrows():
            exp = explainer.explain_instance(row, f)
            print(exp.as_list())
            for i, v in exp.local_exp[1]:
                lime[i] += v
            exps.append(exp)
        lime = lime / len(samples)
        print(lime, np.where(lime > 0.1))
        idx = np.where(lime > 0.1)
        print(cdata.columns[idx])
        for col in cdata.columns[idx].values:
            print(col, np.unique(cdata[col], return_counts=True))
        cluster_lime[c] = lime

    return cluster_lime


def patterns_from_cluster_lime(cluster_lime, data, dataX, labels, lime_threshold=0.01, prefix_sep='#'):
    cluster_patterns = {}
    for c in cluster_lime:
        lime = cluster_lime[c]
        cdata = data[labels == c]
        cdataX = DataFrame(dataX.values[labels == c], columns=dataX.columns)

        patterns = []
        # for ... :
        #
        #
        # cluster_patterns[c] = ...
    return cluster_patterns


def can_predict(model):
    predict_op = getattr(model, "predict", None)
    return callable(predict_op)


def sample_cluster(data, labels, c, sample_frac=0.1, min_sample_size=10):
    indices = (labels == c).astype(int)
    cdata = DataFrame(data.values[indices.astype(bool)], columns=data.columns)
    samples = cdata.sample(frac=sample_frac)
    if len(samples) < min_sample_size:
        if len(cdata) <= min_sample_size:
            samples = cdata
        else:
            samples = cdata.sample(n=min_sample_size)
    return samples
