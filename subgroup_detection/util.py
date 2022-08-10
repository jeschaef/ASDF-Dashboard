import numpy as np
import pandas as pd

def label_data(data, labels, remove_outliers=False):
    """Label the given dataset with clustering labels.

    :param pd.DataFrame data: Dataset
    :param list of int labels: Clustering labels (cluster numbers)
    :param bool remove_outliers: If true, remove the outliers (data points labeled -1)
    :return: Labeled dataset
    :rtype: pd.DataFrame
    """
    labeled = data.drop(labels=['out', 'class'], axis=1)
    labeled['cluster'] = labels
    if remove_outliers:
        labeled = labeled[labeled['cluster'] >= 0]    # remove outliers (cluster -1)
    return labeled


def _scale(data, exclude=[]):
    """Min-max-scale the given dataset inplace.

    Note: All columns have to be numeric.

    :param pd.DataFrame data: Dataset
    :param list of str exclude: Names of columns to exclude from scaling
    :return: Scaled dataset
    :rtype: pd.Dataframe
    """
    if exclude:
        dc = data.copy()

    data = (data - data.min()) / (data.max() - data.min())

    if exclude:
        data[exclude] = dc[exclude]
    return data  # Min-max scaling


def prepare(data, categ_columns=None, label_column='class', prediction_column='out', prefix_sep='#', **kwargs):
    """Transform a given dataset into a numeric dataset by
        - removing the label and prediction column,
        - converting categorical variables into indicators,
        - and min-max-scaling.
        
    :param pd.DataFrame data: Dataset
    :param kwargs: Keyword arguments to pass to the scaling method
    :param  None or list of str categ_columns: List of categorical columns or None. 
        If None, then all columns with type 'category' or 'object' are encoded
    :param str label_column: Name of column with ground-truth class labels
    :param str prediction_column: Name of column with predicted class labels
    :param str prefix_sep: Delimiter to use for one-hot encoding, e.g., sex = {M, F} --> sex#M = {0, 1}.
        Should be a character or string that does not appear in any of the feature names of the dataset.
    :return: Transformed numeric dataset
    :rtype: pd.DataFrame
    """
    data_num = data.copy().drop(labels=[label_column, prediction_column], axis=1)
    data_num = pd.get_dummies(data_num, drop_first=True, columns=categ_columns, prefix_sep=prefix_sep)  # One-hot enc.
    data_num = _scale(data_num, **kwargs)  # Min-max scaling
    return data_num


def _dict_min(d):
    """Minimum value of dictionary values.

    :param dict of int or dict of float d: Dictionary with numeric values.
    :return: Minimum value of the dictionary values.
    :rtype: int or float
    """
    return _dict_apply(d, np.min)


def _dict_max(d):
    """Maximum value of dictionary values.

    :param dict of int or dict of float d: Dictionary with numeric values.
    :return: Maximum value of the dictionary values.
    :rtype: int or float
    """
    return _dict_apply(d, np.max)


def _dict_avg(d):
    """Average value of dictionary values.

    :param dict of int or dict of float d: Dictionary with numeric values.
    :return: Average value of the dictionary values.
    :rtype: int or float
    """
    return _dict_apply(d, np.mean)


def _dict_apply(d, f):
    """Apply a function to the list of values of a dictionary.

    :param dict d: Dictionary.
    :param Callable f: Function.
    :return: Result of the application of f on the values of d.
    :rtype: Any
    """
    return f(list(d.values()))


def _dict_map(d, f):
    """Map the values of a dictionary using a function.

    :param dict d: Dictionary.
    :param Callable f: Function.
    :return: Dictionary with same keys and results of f(d[key])
    :rtype: dict
    """
    return {k: f(v) for k, v in d.items()}
