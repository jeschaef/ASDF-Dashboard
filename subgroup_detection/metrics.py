import operator
from functools import reduce

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

from subgroup_detection.util import _dict_avg, _dict_map, _dict_min, _dict_max, _dict_apply


class UndefinedOperatorError(ValueError):
    def __init__(self, op):
        super().__init__(f"Operator '{op}' is not defined")


def statistical_parity_difference(C):
    """
    Compute the statistical parity difference for the given confusion matrices.

    :param (int, int, int, int, int, int, int, int) C: Confusion matrices of the
        privileged and unprivileged subgroup.
    :return: Statistical parity difference.
    :rtype: float
    """
    tn, fp, fn, tp, tn2, fp2, fn2, tp2 = C
    return acceptance_rate(tn2, fp2, fn2, tp2) - acceptance_rate(tn, fp, fn, tp)


def equal_opportunity_difference(C):
    """
    Compute the equal opportunity difference for the given confusion matrices.

    :param (int, int, int, int, int, int, int, int) C: Confusion matrices of the
        privileged and unprivileged subgroup.
    :return: Equal opportunity difference.
    :rtype: float
    """
    _, _, fn, tp, _, _, fn2, tp2 = C
    return recall(fn2, tp2) - recall(fn, tp)


def average_odds_difference(C):
    """
    Compute the average odds difference for the given confusion matrices.

    :param (int, int, int, int, int, int, int, int) C: Confusion matrices of the
        privileged and unprivileged subgroup.
    :return: Average odds difference.
    :rtype: float
    """
    tn, fp, fn, tp, tn2, fp2, fn2, tp2 = C
    fpr_diff = specificity(tn2, fp2) - specificity(tn, fp)
    tpr_diff = recall(fn2, tp2) - recall(fn, tp)
    return (tpr_diff + fpr_diff) / 2


def acceptance_rate(tn, fp, fn, tp):
    """
    Acceptance rate P / (P + N).

    :param int tn: True negatives.
    :param int fp: False positives.
    :param int fn: False negatives.
    :param int tp: True positives.
    :return: Acceptance rate.
    :rtype: float
    """
    return (tp + fp) / (tp + fp + fn + tn)


def recall(fn, tp):
    """
    Recall score tp / (tp + fn).

    :param int fn: False negatives.
    :param int tp: True positives.
    :return: Recall score.
    :rtype: float
    """
    if tp + fn > 0:
        return tp / (tp + fn)
    return 0


def specificity(tn, fp):
    """
    Specificity score fp / (fp + tn)
    
    :param int tn: True negatives
    :param int fp: False positives.
    :return: Specificity score.
    :rtype: float
    """
    if fp + tn > 0:
        return fp / (fp + tn)
    return 0


def compute_metrics(cluster_patterns, data, pos_label=1):
    """
    Print statistical parity, eq. opportunity and avg. odds difference for the given
    patterns of a clustering.
    
    :param dict of (list of (str, str, Any)) cluster_patterns: List of conjunctive 
        patterns for each cluster
    :param pd.DataFrame data: The original dataset (not preprocessed) 
        incl. ground-truth ('class') and predicted ('out') labels.
    :param int pos_label: Label of the positive class (0 or 1).
    :return: Dataframe with one row for each cluster (pattern)
    :rtype: pd.DataFrame
    """
    res = pd.DataFrame(columns=['Stat. parity diff.', 'Eq. opportunity diff.', 'Avg. odds diff.'])
    for c in cluster_patterns:
        p = cluster_patterns[c]
        C = conf_matrix(data, p, pos_label=pos_label)
        res.loc[c] = [statistical_parity_difference(C), equal_opportunity_difference(C), average_odds_difference(C)]
    return res


def subgroups_to_cluster_patterns(subgroups):
    """
    Transform the given entropy-based subgroups (patterns in form of a dataframe)
    to a dictionary of conjunctive patterns (list of tuples).
    
    :param pd.DataFrame subgroups: Entropy-based subgroups in a DataFrame (each row is a subgroup)
    :return: Dictionary of conjunctive patterns (list of (feature, op, value)-tuples)
    :rtype: list of (str, str, Any)
    """
    cluster_patterns = {}
    for c, row in subgroups.iterrows():
        p = [(fn, '=', val) for fn, val in row.dropna().items()]
        cluster_patterns[c] = p
    return cluster_patterns


def pattern_to_index(data, p):
    """
    Transform the patterns on the given dataset to a filter on the index (boolean array).
    
    :param pd.DataFrame data: The original dataset (not preprocessed).
    :param list of (str, Any, Any) p: Conjunctive pattern (e.g., for a single cluster).
    :return: Filter on the index of the dataset (boolean array).
    :rtype: list of bool
    """
    conditions = []
    for pattern in p:
        col, op, val = pattern
        if op == '=':
            conditions.append(data[col] == val)
        elif op == '!=':
            conditions.append(data[col] != val)
        elif op == '<=':
            conditions.append(data[col] <= val)
        elif op == '>=':
            conditions.append(data[col] >= val)
        else:
            raise UndefinedOperatorError(op)
    return reduce(operator.and_, conditions)


def conf_matrix(data, p, pos_label=1):
    """
    Get the confusion matrices of the privileged and unprivileged subgroup.
    
    :param pd.DataFrame data: Dataset with ground-truth and predicted labels
    :param list of (str, str, Any) p: Conjunctive pattern defining a single subgroup
    :param int pos_label: Label of the positive (favorable) class (0 or 1).
    :return: tn, fp, fn, tp, tn2, fp2, fn2, tp2 (privileged & unprivileged subgroup)
    :rtype: (int, int, int, int, int, int, int, int)
    """
    y_true = data['class']
    y_pred = data['out']

    idx = pattern_to_index(data, p)
    y_true_group = y_true[idx]
    y_pred_group = y_pred[idx]

    y_true_rest = y_true[~idx]
    y_pred_rest = y_pred[~idx]

    if pos_label == 1:
        tn, fp, fn, tp = confusion_matrix(y_true_group, y_pred_group, labels=[0, 1]).ravel()
        tn2, fp2, fn2, tp2 = confusion_matrix(y_true_rest, y_pred_rest, labels=[0, 1]).ravel()
    elif pos_label == 0:
        tp, fn, fp, tn = confusion_matrix(y_true_group, y_pred_group, labels=[0, 1]).ravel()
        tp2, fn2, fp2, tn2 = confusion_matrix(y_true_rest, y_pred_rest, labels=[0, 1]).ravel()
    return tn, fp, fn, tp, tn2, fp2, fn2, tp2


def pattern_support(p, data):
    """
    Compute the support of a given conjunctive pattern, i.e., the ratio
    of instances that satisfy the pattern.
    
    :param list of (str, str, Any) p: Conjunctive pattern of the form 
        '(col op val) ^ (col2 op val2) ^ ...' where operators in the form of
        booleans are '=' (True) or '!=' (False). The conjunctive pattern is
        presented as a list of the individual attribute-value pairs.
    :param pd.DataFrame data: The original dataset (not preprocessed).
    :return: Support of the conjunctive pattern
    :rtype: float
    """
    idx = pattern_to_index(data, p)
    return idx.sum() / len(data)


def cluster_pattern_support(cluster_patterns, data):
    """
    Compute the support of each pattern in the dataset.
    
    :param dict of (list of (str, str, Any)) cluster_patterns: Dict of conjunctive
        patterns for each cluster.
    :param pd.DataFrame data: The original dataset (not preprocessed).
    :return: Support per pattern
    :rtype: dict of float
    """
    return {c: pattern_support(p, data) for c, p in cluster_patterns.items()}


def containment_score(p, p_list, data):
    """
    Compute the containment score of the given pattern in comparison to the
    patterns from the list.

    :param list of (str, str, Any) p: Single conjunctive pattern.
    :param list of (list of (str, str, Any)) p_list: List of conjunctive patterns.
    :param pd.DataFrame data: The original dataset (not preprocessed).
    :return: Containment score of p compared to all patterns in p_list
    :rtype: float
    """
    idx = pattern_to_index(data, p)
    scores = []
    for p2 in p_list:
        idx2 = pattern_to_index(data, p2)
        scores.append((idx & idx2).sum() / idx.sum())
    return np.max(scores)


def cluster_containment_score(cluster_patterns, data):
    """
    Compute the containment score for conjunctive patterns in a one-vs-rest fashion,
    i.e., compute the containment of each of the patterns in comparison to all other
    patterns except the selected.

    :param dict of (int, list of (str, str, Any)) cluster_patterns: Dict of conjunctive
        patterns for each cluster.
    :param pd.DataFrame data: The original dataset (not preprocessed).
    :return: Containment score per pattern
    :rtype: dict of float
    """
    containment = {}
    for c, p in cluster_patterns.items():
        other_patterns = cluster_patterns.copy()
        other_patterns.pop(c)
        containment[c] = containment_score(p, other_patterns.values(), data)
    return containment


def cluster_pattern_size(cluster_patterns):
    """Compute the pattern sizes of the given patterns.

    :param dict of (list of (str, str, Any)) cluster_patterns: Dict of conjunctive
        patterns for each cluster.
    :return: Sizes of the patterns
    :rtype: dict of float
    """
    return _dict_map(cluster_patterns, len)


def average_pattern_size(cluster_patterns):
    """Compute the average pattern size over the given patterns.

    :param dict of (list of (str, str, Any)) cluster_patterns: Dict of conjunctive
        patterns for each cluster.
    :return: Average pattern size
    :rtype: float
    """
    return _dict_avg(cluster_pattern_size(cluster_patterns))


def fidelity(p, c, data, labels):
    """Compute the fidelity of the given pattern on the given dataset.

    :param list of (str, str, Any) p: Single conjunctive pattern
    :param int c: Cluster number
    :param pd.DataFrame data: The original dataset (not preprocessed).
    :param list of int labels: Cluster labels
    :return: Fidelity of p
    :rtype: float
    """
    idx = pattern_to_index(data, p)
    cluster_idx = labels == c
    return (idx & cluster_idx).sum() / idx.sum()


def cluster_fidelity(cluster_patterns, data, labels):
    """Compute the fidelity of the given dict of conjunctive patterns for each cluster.

    :param dict of (list of (str, str, Any)) cluster_patterns: Dict of conjunctive
        patterns for each cluster.
    :param pd.DataFrame data: The original dataset (not preprocessed).
    :param list of int labels: Cluster labels
    :return: Fidelity of each pattern
    :rtype: dict of float
    """
    # Compute the fidelity for each pattern/cluster
    return {c: fidelity(p, c, data, labels) for c, p in cluster_patterns.items()}


def cluster_coverage(cluster_patterns, data):
    """Compute the coverage of the given dict of conjunctive patterns on the dataset,
    i.e., the fraction of instances covered by at least one pattern.

    :param dict of (list of (str, str, Any)) cluster_patterns: Dict of conjunctive
        patterns for each cluster.
    :param pd.DataFrame data: The original dataset (not preprocessed).
    :return: Coverage of the patterns on the dataset
    :rtype: float
    """
    idx = [False] * len(data)
    for c, p in cluster_patterns.items():
        idx = idx | pattern_to_index(data, p)       # concatenate all index lists with logical or
    return idx.sum() / len(data)        # ratio of instances affected by a pattern


def pattern_jaccard(p1, p2):
    """Given two conjunctive patterns p1 and p2 compute their Jaccard similarity:

    .. math::
        |p_1 \cap p_2| / |p_1 \cup p_2|

    :param list of (str, str, Any) p1: Conjunctive pattern.
    :param list of (str, str, Any) p2: Conjunctive pattern.
    :return: Jaccard similarity of the two patterns
    :rtype: float
    """
    return len(list(set(p1) & set(p2))) / len(list(set(p1) | set(p2)))


def cluster_pattern_jaccard(cluster_patterns_1, cluster_patterns_2):
    return {c: pattern_jaccard(p1, p2)
            for (c, p1), (_, p2) in zip(cluster_patterns_1.items(), cluster_patterns_2.items())}


def cluster_pattern_avg_jaccard(cluster_patterns_1, cluster_patterns_2):
    return _dict_avg(cluster_pattern_jaccard(cluster_patterns_1, cluster_patterns_2))


def print_pattern_metrics(cluster_patterns, data, labels):
    size = cluster_pattern_size(cluster_patterns)
    print(f"Pattern size:\t\t{_dict_avg(size)} ({_dict_min(size)} - {_dict_max(size)})")
    support = cluster_pattern_support(cluster_patterns, data)
    print(f"Support:\t\t{_dict_avg(support)} ({_dict_min(support)} - {_dict_max(support)})")
    print(f"Coverage:\t\t{cluster_coverage(cluster_patterns, data)}")
    containment = cluster_containment_score(cluster_patterns, data)
    print(f"Containment scores:\t{_dict_avg(containment)} ({_dict_min(containment)} - {_dict_max(containment)})")
    fidelity = cluster_fidelity(cluster_patterns, data, labels)
    print(f"Fidelity: \t\t{_dict_avg(fidelity)} ({_dict_min(fidelity)} - {_dict_max(fidelity)})")
