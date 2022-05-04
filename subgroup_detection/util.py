import pandas as pd

def label_data(data, labels, remove_outliers=False):
    """
    Label the given dataset with clustering labels.
    @param data: Dataset
    @type data: pd.DataFrame
    @param labels: Clustering labels (cluster numbers)
    @type labels: list
    @param remove_outliers: If true, remove the outliers (data points labeled -1)
    @type remove_outliers: bool
    @return: Labeled dataset
    @rtype: pd.DataFrame
    """
    labeled = data.drop(labels=['out', 'class'], axis=1)
    labeled['cluster'] = labels
    if remove_outliers:
        labeled = labeled[labeled['cluster'] >= 0]    # remove outliers (cluster -1)
    return labeled


def _scale(data, exclude=[]):
    """
    Min-max-scale the given dataset inplace.
    Note: All columns have to be numeric.
    @param data: Dataset
    @type data: pd.DataFrame
    @param exclude: Names of columns to exclude from scaling
    @type exclude: list of str
    @return: Scaled dataset
    @rtype: pd.Dataframe
    """
    if exclude:
        dc = data.copy()

    data = (data - data.min()) / (data.max() - data.min())

    if exclude:
        data[exclude] = dc[exclude]
    return data  # Min-max scaling


def prepare(data, categ_columns=None, **kwargs):
    """
    Transform a given dataset into a numeric dataset by
        - removing the columns 'cluster', 'out' and 'class',
        - converting categorical variables into indicators,
        - and min-max-scaling.
    @param data: Dataset
    @type data: pd.DataFrame
    @param kwargs: Keyword arguments to pass to the scaling method
    @type kwargs: Keyword arguments
    @param categ_columns: List of categorical columns or None. If None, then all columns
    with type 'category' or 'object' are encoded
    @type categ_columns: None or list of str
    @return: Transformed numeric dataset
    @rtype: pd.DataFrame
    """
    data_num = data.copy().drop(labels=['cluster', 'out', 'class'], axis=1)
    data_num = pd.get_dummies(data_num, drop_first=True, columns=categ_columns)  # One hot encoding
    data_num = _scale(data_num, **kwargs)  # Min-max scaling
    return data_num