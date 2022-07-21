import operator
from functools import reduce

from sklearn.metrics import confusion_matrix


def statistical_parity_difference(conf_matrix):
    """
    Compute the statistical parity difference for the given confusion matrices.
    :param conf_matrix: Confusion matrices of the privileged and unprivileged subgroup.
    :return: Statistical parity difference.
    """
    tn, fp, fn, tp, tn2, fp2, fn2, tp2 = conf_matrix
    acc_rate_priv = (tp + fp) / (tp + fp + fn + tn)
    acc_rate_unpriv = (tp2 + fp2) / (tp2 + fp2 + fn2 + tn2)
    return acc_rate_unpriv - acc_rate_priv


def equal_opportunity_difference(conf_matrix):
    """
    Compute the equal opportunity difference for the given confusion matrices.
    :param conf_matrix: Confusion matrices of the privileged and unprivileged subgroup.
    :return: Equal opportunity difference.
    """
    tn, fp, fn, tp, tn2, fp2, fn2, tp2 = conf_matrix
    tpr_priv = tp / (tp + fn)
    tpr_unpriv = tp2 / (tp2 + fn2)
    return tpr_unpriv - tpr_priv


def average_odds_difference(conf_matrix):
    """
    Compute the average odds difference for the given confusion matrices.
    :param conf_matrix: Confusion matrices of the privileged and unprivileged subgroup.
    :return: Average odds difference.
    """
    tn, fp, fn, tp, tn2, fp2, fn2, tp2 = conf_matrix
    fpr_priv = fp / (fp + tn)
    fpr_unpriv = fp2 / (fp2 + tn2)
    fpr_diff = fpr_unpriv - fpr_priv

    tpr_priv = tp / (tp + fn)
    tpr_unpriv = tp2 / (tp2 + fn2)
    tpr_diff = tpr_unpriv - tpr_priv
    return (tpr_diff + fpr_diff) / 2


def print_metrics(cluster_rules, data, pos_label=1):
    """
    Print statistical parity, eq. opportunity and avg. odds difference for the given rules of
    a clustering.
    :param cluster_rules: Set of rules for each cluster
    :param data: The original dataset (not preprocessed) incl. ground-truth ('class')
    and predicted ('out') labels.
    :param pos_label: Label of the positive class (0 or 1).
    """
    for c in cluster_rules:
        rules = cluster_rules[c]
        C = conf_matrix(data, rules, pos_label=pos_label)

        print("Cluster", c)
        print('Stat. parity diff.\t', statistical_parity_difference(C))
        print('Eq. opportunity diff.\t', equal_opportunity_difference(C))
        print('Avg. odds diff.\t\t', average_odds_difference(C))

def rules_to_index(data, rules):
    """
    Transform the rules on the given dataset to a filter on the index (boolean array).
    :param data: The original dataset (not preprocessed).
    :param rules: Ruleset (e.g., for a single cluster).
    :return: Filter on the index of the dataset (boolean array).
    """
    conditions = []
    for rule in rules:
        col, equals, val = rule
        if equals:
            conditions.append(data[col] == val)
        else:
            conditions.append(data[col] != val)
    return reduce(operator.and_, conditions)


def conf_matrix(data, rules, pos_label=1):
    """
    Get the confusion matrices of the privileged and unprivileged subgroup.
    :param data: Dataset with ground-truth and predicted labels
    :param rules: Rules defining subgroup
    :param pos_label: Label of the positive (favorable) class (0 or 1).
    :return: tn, fp, fn, tp, tn2, fp2, fn2, tp2 (privileged & unprivileged)
    """
    y_true = data['class']
    y_pred = data['out']

    idx = rules_to_index(data.drop(columns=['out', 'class']), rules)
    y_true_group = y_true[idx]
    y_pred_group = y_pred[idx]

    y_true_rest = y_true[~idx]
    y_pred_rest = y_pred[~idx]

    print(y_true_group.shape, y_true_rest.shape)
    if pos_label == 1:
        tn, fp, fn, tp = confusion_matrix(y_true_group, y_pred_group, labels=[0, 1]).ravel()
        tn2, fp2, fn2, tp2 = confusion_matrix(y_true_rest, y_pred_rest, labels=[0, 1]).ravel()
    elif pos_label == 0:
        tp, fn, fp, tn = confusion_matrix(y_true_group, y_pred_group, labels=[0, 1]).ravel()
        tp2, fn2, fp2, tn2 = confusion_matrix(y_true_rest, y_pred_rest, labels=[0, 1]).ravel()
    return tn, fp, fn, tp, tn2, fp2, fn2, tp2
