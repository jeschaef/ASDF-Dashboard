import operator
from functools import reduce

import pandas as pd
from sklearn.metrics import confusion_matrix


def statistical_parity_difference(conf_matrix):
    """
    Compute the statistical parity difference for the given confusion matrices.
    :param conf_matrix: Confusion matrices of the privileged and unprivileged subgroup.
    :return: Statistical parity difference.
    """
    tn, fp, fn, tp, tn2, fp2, fn2, tp2 = conf_matrix
    return acceptance_rate(tn2, fp2, fn2, tp2) - acceptance_rate(tn, fp, fn, tp)


def equal_opportunity_difference(conf_matrix):
    """
    Compute the equal opportunity difference for the given confusion matrices.
    :param conf_matrix: Confusion matrices of the privileged and unprivileged subgroup.
    :return: Equal opportunity difference.
    """
    _, _, fn, tp, _, _, fn2, tp2 = conf_matrix
    return  recall(fn2, tp2) - recall(fn, tp)


def average_odds_difference(conf_matrix):
    """
    Compute the average odds difference for the given confusion matrices.
    :param conf_matrix: Confusion matrices of the privileged and unprivileged subgroup.
    :return: Average odds difference.
    """
    tn, fp, fn, tp, tn2, fp2, fn2, tp2 = conf_matrix
    fpr_diff = specificity(tn2, fp2) - specificity(tn, fp)
    tpr_diff = recall(fn2, tp2) - recall(fn, tp)
    return (tpr_diff + fpr_diff) / 2


def acceptance_rate(tn, fp, fn, tp):
    """
    Acceptance rate P / (P + N).
    :param tn: True negatives.
    :param fp: False positives.
    :param fn: False negatives.
    :param tp: True positives.
    :return: Acceptance rate.
    """
    return (tp + fp) / (tp + fp + fn + tn)


def recall(fn, tp):
    """
    Recall score tp / (tp + fn).
    :param fn: False negatives.
    :param tp: True positives.
    :return: Recall score.
    """
    if tp + fn > 0:
        return tp / (tp + fn)
    return 0


def specificity(tn, fp):
    """
    Specificity score fp / (fp + tn)
    :param tn: True negatives
    :param fp: False positives.
    :return: Specificity score.
    """
    if fp + tn > 0:
        return fp / (fp + tn)
    return 0


def compute_metrics(cluster_patterns, data, pos_label=1):
    """
    Print statistical parity, eq. opportunity and avg. odds difference for the given
    patterns of a clustering.
    :param cluster_patterns: List of conjunctive patterns for each cluster
    :param data: The original dataset (not preprocessed) incl. ground-truth ('class')
    and predicted ('out') labels.
    :param pos_label: Label of the positive class (0 or 1).
    :return: Dataframe with one row for each cluster (pattern)
    """
    res = pd.DataFrame(columns=['Stat. parity diff.', 'Eq. opportunity diff.', 'Avg. odds diff.'])
    for c in cluster_patterns:
        patterns = cluster_patterns[c]
        C = conf_matrix(data, patterns, pos_label=pos_label)
        res.loc[c] = [statistical_parity_difference(C), equal_opportunity_difference(C), average_odds_difference(C)]
    return res


def patterns_to_index(data, p):
    """
    Transform the patterns on the given dataset to a filter on the index (boolean array).
    :param data: The original dataset (not preprocessed).
    :param p: Conjunctive pattern (e.g., for a single cluster).
    :return: Filter on the index of the dataset (boolean array).
    """
    conditions = []
    for pattern in p:
        col, equals, val = pattern
        if equals:
            conditions.append(data[col] == val)
        else:
            conditions.append(data[col] != val)
    return reduce(operator.and_, conditions)


def conf_matrix(data, patterns, pos_label=1):
    """
    Get the confusion matrices of the privileged and unprivileged subgroup.
    :param data: Dataset with ground-truth and predicted labels
    :param patterns: Patterns defining subgroup
    :param pos_label: Label of the positive (favorable) class (0 or 1).
    :return: tn, fp, fn, tp, tn2, fp2, fn2, tp2 (privileged & unprivileged)
    """
    y_true = data['class']
    y_pred = data['out']

    idx = patterns_to_index(data, patterns)
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
    Compute the support of a given conjunctive pattern.
    :param p: Conjunctive pattern of the form (col T/F val) ^ (col2 T/F val2) ^ ...
    where operators are = or !=.
    :type p: List of (str, bool, Any)
    :param data: The original dataset (not preprocessed).
    :type data: pd.DataFrame
    :return: Support of the conjunctive pattern
    :rtype: float
    """
    idx = patterns_to_index(data, p)
    return idx.sum() / len(data)


def containment_score(p, p_set, data):
    idx = patterns_to_index(data, p)

    scores = []
    for p2 in p_set:
        idx2 = patterns_to_index(data, p2)
        scores.append((idx & idx2).sum() / idx.sum())

    return scores.max()


