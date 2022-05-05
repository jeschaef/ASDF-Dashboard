import json
import warnings

import sklearn.base
from aif360.sklearn import metrics as mtr
from aif360.sklearn.utils import check_groups
from sklearn.exceptions import UndefinedMetricWarning
from sklearn.metrics import accuracy_score, f1_score, silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.base import ClusterMixin
import pandas as pd
from pandas import DataFrame, Series
import numpy as np

from subgroup_detection.entropy import *
from subgroup_detection.util import *
from subgroup_detection.clustering import *


def ground_truth_protected(data, protected):
    """
    Create a ground-truth labeled series from the dataset.
    @param data: Dataset with ground-truth labels (column 'class')
    @type data: DataFrame
    @param protected: Names of the protected attributes
    @type protected: list of str
    @return: Series of ground-truth labels indexed by protected attribute values
    @rtype: Series
    """

    ground_truth = data['class'].copy()

    # MultiIndex over protected attributes + original id
    multi_idx = pd.MultiIndex.from_frame(data[protected])
    idx_arr = np.array(multi_idx.codes)  # codes from protected attribute values
    idx_arr = np.concatenate(([data.index.values], idx_arr), axis=0)  # concatenate with original id

    # add multiindex to ground truth series
    ground_truth.index = pd.MultiIndex.from_arrays(idx_arr, names=['id'] + protected)
    return ground_truth


# Get priveleged group from protected attribute values
def priveleged_group(data, protected, prot_vals):
    """
    Get the privileged group from the protected attributes values.
    @param data: Dataset
    @type data: DataFrame
    @param protected: Names of the protected attributes
    @type protected: list of str
    @param prot_vals: Protected attribute values that define the (un)privileged group
    @type prot_vals: list of obj
    @return: Tuple with index values for the privileged group (ground-truth multi-index)
    @rtype: (int, ...)
    """
    # Multiindex over protected attributes
    multi_idx = pd.MultiIndex.from_frame(data[protected])

    # Get index of protected values
    priv_group = []
    for i, v in enumerate(prot_vals):
        l = multi_idx.levels[i].values
        priv_group = priv_group + list(np.where(l == v)[0])

    return tuple(priv_group)


def cluster_fairness(data, cluster_labels, groups, pos_label):
    """
    Compute different fairness metrics for the given clustering and subgroups.
    @param data: Dataset of n instances incl. columns 'out' (predicted class) and 'class' (groundtruth class).
    @type data: DataFrame
    @param cluster_labels: Cluster assignment for each instance
    @type cluster_labels: list of int
    @param groups: Protected subgroups (patterns of attribute-value assignments) to assess the classifiers fairness.
    @type groups: DataFrame
    @param pos_label: Value of the predicted/true classification label (0 or 1)
    @type pos_label: int
    @return: General fairness, subgroup fairness and protected groups
    @rtype: (DataFrame, DataFrame, dict of dict)
    """
    # Ground truth for clusters
    protected = ['cluster']
    data['cluster'] = cluster_labels
    y_pred = data['out']
    gt = ground_truth_protected(data, protected)
    grouped = data.groupby('cluster')

    # Compute general metrics
    base_rate = [mtr.base_rate(gt, y_pred, pos_label=0), mtr.base_rate(gt, y_pred)]
    sensitivity = [mtr.sensitivity_score(gt, y_pred, pos_label=0), mtr.sensitivity_score(gt, y_pred)]
    specificity = [mtr.specificity_score(gt, y_pred, pos_label=0), mtr.specificity_score(gt, y_pred)]
    accuracy = accuracy_score(data['class'], y_pred)
    f1 = f1_score(data['class'], y_pred)

    general_fairness = DataFrame({
        'base_rate': base_rate,
        'sensitivity': sensitivity,
        'specificity': specificity,
        'accuracy': [accuracy, accuracy],
        'f1_score': [f1, f1],
    }, index=[0, 1])

    # Subgroup fairness metrics initialization
    num_cluster = max(cluster_labels) + 1
    priv_groups = {}
    is_duplicated = groups.duplicated()  # to skip duplicate subgroups
    subgroup_fairness = DataFrame(0, index=list(range(num_cluster)),
                                  columns=[  # 'priv_group',
                                      'c_stat_par', 'c_eq_opp', 'c_avg_odds', 'c_acc',
                                      'g_stat_par', 'g_eq_opp', 'g_avg_odds', 'g_acc', ])

    for i, cluster in grouped:

        # Skip outliers
        if i < 0:
            continue

        # Privileged group for cluster
        pg = priveleged_group(data, protected, [i])

        # Compute cluster fairness
        cluster_stat_par, cluster_eq_opp, cluster_avg_odds, cluster_acc = \
            _subgroup_fairness(gt, y_pred, protected, pg, pos_label, cluster['class'], cluster['out'])

        # Group fairness
        group = groups.iloc[i].dropna()
        priv_groups[i] = group.to_dict()

        # Skip empty or duplicate groups
        if group.empty or is_duplicated[i]:
            group_stat_par = group_eq_opp = group_avg_odds = group_acc = np.NaN

        else:
            group_protected = group.index.tolist()

            # ground truth of all (protected attributes from group)
            gt_group_prot = ground_truth_protected(data, group_protected)
            group_pg = priveleged_group(data, group_protected, group.values.tolist())

            test, _ = check_groups(gt_group_prot, group_protected)
            idx = (test == group_pg)
            group_gt = gt_group_prot[idx]  # ground truth for data in group only (subset of whole dataset)
            group_out = y_pred[idx]

            # Compute group fairness
            group_stat_par, group_eq_opp, group_avg_odds, group_acc = \
                _subgroup_fairness(gt_group_prot, y_pred, group_protected, group_pg, pos_label, group_gt, group_out)

        # Store metrics
        subgroup_fairness.iloc[i] = [cluster_stat_par, cluster_eq_opp, cluster_avg_odds, cluster_acc,
                                     group_stat_par, group_eq_opp, group_avg_odds, group_acc]

    return general_fairness, subgroup_fairness, priv_groups


def _subgroup_fairness(y_true, y_pred, protected, pg, pos_label, group_true, group_pred):
    """
    Compute different subgroup fairness metrics.
    @param y_true: Ground-truth data in a dataframe indexed by the protected attributes
    @type y_true: DataFrame
    @param y_pred: Predicted labels of whole dataset
    @type y_pred: list of int
    @param protected: Protected attribute names
    @type protected: list of str
    @param pg: Protected subgroup definition (attribute values for protected attributes)
    @type pg: list of obj
    @param pos_label: Positive (favorable) label (0 or 1)
    @type pos_label: int
    @param group_true: Ground-truth labels for the protected group
    @type group_true: list of int
    @param group_pred: Predicted labels for the protected group
    @type group_pred: list of int
    @return: Subgroup fairness for metrics statistical parity, equal opportunity,
    equalized odds and subgroup accuracy.
    @rtype: (float, float, float, float)
    """
    stat_par = mtr.statistical_parity_difference(y_true, y_pred, prot_attr=protected,
                                                 priv_group=pg, pos_label=pos_label)

    eq_opp = mtr.equal_opportunity_difference(y_true, y_pred, prot_attr=protected,
                                              priv_group=pg, pos_label=pos_label)

    avg_odds = mtr.average_odds_difference(y_true, y_pred, prot_attr=protected,
                                           priv_group=pg, pos_label=pos_label)

    # disp_imp = mtr.disparate_impact_ratio(gt, y_pred, prot_attr=protected,
    #                                               priv_group=pg, pos_label=pos_label)
    acc = accuracy_score(group_true, group_pred)

    return stat_par, eq_opp, avg_odds, acc


def print_cluster_fairness(data, cluster_labels, groups, pos_label):
    # Compute fairness metrics
    general_fairness, subgroup_fairness = cluster_fairness(data, cluster_labels, groups, pos_label)

    # General metrics
    print('General metrics:')
    print('\tBase rate:', '%.4f' % general_fairness.base_rate.iloc[1], '(class=1),',
          '%.4f' % general_fairness.base_rate.iloc[0], '(class=0)')
    print('\tSensitivity score (TPR, recall):', '%.4f' % general_fairness.sensitivity.iloc[1], '(class=1),',
          '%.4f' % general_fairness.sensitivity.iloc[0], '(class=0)')
    print('\tSpecificity score (TNR):', '%.4f' % general_fairness.specificity.iloc[1], '(class=1),',
          '%.4f' % general_fairness.specificity.iloc[0], '(class=0)')
    print('\tAccuracy:', '%.4f' % general_fairness.accuracy.iloc[0])
    print('\tF1-Score:', '%.4f' % general_fairness.f1_score.iloc[0])
    print('')

    # Subgroup
    for i, row in subgroup_fairness.iterrows():
        print('Cluster', i, '-->', row.priv_group)

        # Print it
        print('\tAvg odds diff:', '%.4f' % row.c_avg_odds, '(cluster),', row.g_avg_odds, '(group)')
        print('\tStat. parity diff:', '%.4f' % row.c_stat_par, '(cluster),', row.g_stat_par, '(group)')
        print('\tAccuracy:', '%.4f' % row.c_acc, '(cluster),', row.g_acc, '(group)')


def test_model_fairness(model, data, pos_label=1, threshold=0.65, categ_columns=None):
    """

    @param model: Clustering model to train on the data
    (Note: The clustering model is not the target of the fairness assessment)
    @type model: ClusterMixin
    @param data: Dataset with ground-truth (column 'class') and predicted labels (column 'out').
    @type data: DataFrame
    @param pos_label: Positive (favorable) label (0 or 1)
    @type pos_label: int
    @param threshold: Normalized feature entropy threshold between 0 and 1
    @type threshold: float
    @param categ_columns: List of categorical columns or None. If None, then all columns
    with type 'category' or 'object' are encoded
    @type categ_columns: None or list of str
    @return: Model fairness and other statistics
    @rtype: FairnessResult
    """
    # Train clustering model
    x = prepare(data, categ_columns)
    m = model.fit(x)
    clustering = m.labels_

    # Set clustering labels
    data_clustered = data.copy()
    data_clustered['cluster'] = clustering
    data_clustered = data_clustered.drop(labels=['out', 'class'], axis=1)
    # data_clustered = data_clustered[data_clustered['cluster'] >= 0]  # remove outliers (cluster -1)

    # Subgroups via normalized cluster entropy
    g = normalized_entropy_groups(data_clustered, threshold=threshold)

    # Compute fairness metrics
    with warnings.catch_warnings():  # catch warnings in this block
        warnings.simplefilter("ignore", category=UndefinedMetricWarning)
        general_fairness, subgroup_fairness, priv_groups = cluster_fairness(data, clustering, g,
                                                                                pos_label=pos_label)

    # Return results from subgroup fairness computation
    return FairnessResult.create(general_fairness, subgroup_fairness, g, x, m)


def benchmark_clustering(models, dataset, pos_label=1):
    """
    Benchmark a set of clustering models and return results for the model
    with maximal value for the product of silhouette score and mean absolute
    cluster accuracy error.
    @param models: List of cluster models
    @type models: list of ClusterMixin
    @param dataset: Dataset with ground-truth (column 'class') and predicted labels (column 'out').
    @type dataset: pd.DataFrame
    @param pos_label: Positive (favorable) label (0 or 1)
    @type pos_label: int
    @return: Fairness and benchmark result of the best model that was tested:
    FairnessResult, mean absolute cluster accuracy error, silhouette score, params of the model)
    @rtype: (FairnessResult, float, float, dict)
    """
    max_error = 0
    max_sil = -1
    max_prod = -1
    best_fair = None
    best_params = None

    for m in models:
        fair_res = test_model_fairness(m, dataset, pos_label=pos_label)

        if max_prod < fair_res.c_acc.mean_abs_err * fair_res.cvi.sil:
            max_error = fair_res.c_acc.mean_abs_err
            max_sil = fair_res.cvi.sil
            max_prod = max_error * max_sil
            best_fair = fair_res
            best_params = m.get_params()

    print(
        f"Highest absolute mean error={max_error:0.4f} and silhouette={max_sil:0.4f} "
        f"for params={best_params} (duplication={best_fair.duplication})")
    print(best_fair.fair)

    return best_fair, max_error, max_sil, best_params


class FairnessResult:

    @classmethod
    def create(cls, general_fairness, subgroup_fairness, g, x, m):
        res = cls()
        res.fair = DataFrame(data={'mean': subgroup_fairness.mean().values,
                                    'std': subgroup_fairness.std().values,
                                    'abs_mean': subgroup_fairness.abs().mean().values,
                                    'abs_std': subgroup_fairness.abs().std().values},
                              index=subgroup_fairness.columns)

        # Accuracy error (cluster)
        c_acc_err = subgroup_fairness.c_acc - general_fairness.accuracy.iloc[0]
        res.c_acc = Series(data={'min_err': c_acc_err.min(),
                                  'max_err': c_acc_err.max(),
                                  'mean_err': c_acc_err.mean(),
                                  'std_err': c_acc_err.std(),
                                  'mean_abs_err': c_acc_err.abs().mean(),
                                  'std_abs_err': c_acc_err.abs().std()})

        # Accuracy error (group)
        g_acc_err = subgroup_fairness.g_acc - general_fairness.accuracy.iloc[0]
        res.g_acc = Series(data={'min_err': g_acc_err.min(),
                                  'max_err': g_acc_err.max(),
                                  'mean_err': g_acc_err.mean(),
                                  'std_err': g_acc_err.std(),
                                  'mean_abs_err': g_acc_err.abs().mean(),
                                  'std_abs_err': g_acc_err.abs().std()})

        # Groups
        res.subgroups = g
        res.duplication = subgroup_fairness.g_acc.isna().sum() / len(g)  # rate of duplicate groups

        # Cluster validation
        # res.model = m        # cannot be serialized easily
        res.clustering = m.labels_
        res.cvi = validate_clustering(x, m.labels_)

        # Raw data
        res.raw = subgroup_fairness

        return res


    def to_json(self):
        print(type(self.subgroups), type(self.cvi))
        return json.dumps({
            "fair": self.fair.to_json(),
            "c_acc": self.c_acc.to_json(),
            "g_acc": self.g_acc.to_json(),
            "subgroups": self.subgroups.to_json(),
            "duplication": self.duplication,
            "clustering": self.clustering.tolist(),
            "cvi": self.cvi.to_json(),
            "raw": self.raw.to_json()
        })


    @classmethod
    def from_json(cls, fair_json):
        res = cls()
        parsed = json.loads(fair_json)

        res.fair = parsed["fair"]
        res.c_acc = parsed["c_acc"]
        res.g_acc = parsed["g_acc"]
        res.subgroups = parsed["subgroups"]
        res.duplication = parsed["duplication"]
        res.clustering = parsed["clustering"]
        res.cvi = parsed["cvi"]
        res.raw = parsed["raw"]

        return res