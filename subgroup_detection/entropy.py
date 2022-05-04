import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb
from ipywidgets import interact
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch
from subgroup_detection import util


def normalized_entropy(data):
    """
    Compute the normalized feature entropy for each cluster.
    @param data: Dataset with one additional column 'cluster' containing the clustering labels.
    @type data: pd.DataFrame
    @return: Normalized feature entropy per cluster
    @rtype: pd.DataFrame
    """
    # Create output dataframe with same columns as x and one row per cluster
    num_clusters = data['cluster'].max() + 1
    clus_size = data.groupby('cluster').size()
    clusdf = pd.DataFrame(0, index=np.arange(num_clusters), columns=data.columns.drop('cluster'))

    # Iterate over all features
    for fn in clusdf.columns:
        grouped = data.groupby(['cluster', fn])

        # Compute entropy H = - sum[Px * log(Px)]
        Px = grouped.size() / clus_size  # value frequency
        entropy = - (Px * np.log(Px))
        H = entropy.groupby('cluster', sort=True).sum()

        # normalize by H_max = log(N)
        N = data[fn].nunique()
        H_max = np.log(N)
        clusdf[fn] = H / H_max

    return clusdf


def normalized_entropy_cluster(data):
    """
    Compute the normalized feature entropy for each cluster (normalize feature entropy
    for values present in cluster, NOT entire dataset).
    @param data: Dataset with one additional column 'cluster' containing the clustering labels.
    @type data: pd.DataFrame
    @return: Normalized feature entropy per cluster
    @rtype: pd.DataFrame
    """
    # Create output dataframe with same columns as x and one row per cluster
    num_clusters = data['cluster'].max() + 1
    clus_size = data.groupby('cluster').size()
    clusdf = pd.DataFrame(0, index=np.arange(num_clusters), columns=data.columns.drop('cluster'))

    # Iterate over all features
    for fn in clusdf.columns:
        grouped = data.groupby(['cluster', fn])

        # Compute entropy H = - sum[Px * log(Px)]
        Px = grouped.size() / clus_size  # relative value frequency
        entropy = - (Px * np.log(Px))
        H = entropy.groupby('cluster', sort=True).sum()
        # print(H)

        # normalize by H_max = log(N)
        N = data[['cluster', fn]].groupby('cluster').nunique()
        H_max = np.log(N.values)
        clusdf[fn] = H.div(H_max.T[0], axis=0).fillna(0)   # div by 0 (from log(1)) causes NaN values

    return clusdf


def relative_entropy(data):
    """
    Compute the relative feature entropy for each cluster.
    @param data: Dataset with one additional column 'cluster' containing the clustering labels.
    @type data: pd.DataFrame
    @return: Relative feature entropy per cluster
    @rtype: pd.DataFrame
    """
    # Create output dataframe with same columns as x and one row per cluster
    num_clusters = data['cluster'].max() + 1
    clus_size = data.groupby('cluster').size()
    clusdf = pd.DataFrame(0, index=np.arange(num_clusters), columns=data.columns.drop('cluster'))

    # Compute global frequencies Qx per feature
    data_size = len(data)
    Qx = {fn: data.groupby(fn).size() / data_size for fn in clusdf.columns}

    # Compute relative entropy=sum[Px * log(Px / Qx)] (Kullback-Leibler divergence)
    for fn in clusdf.columns:
        grouped = data.groupby(['cluster', fn])
        Px = grouped.size() / clus_size

        # Iterate over clusters
        relative_entropies = np.zeros(num_clusters)
        for i in range(num_clusters):
            entropy = Px[i] * np.log(Px[i] / Qx[fn])
            relative_entropies[i] = entropy.sum()
        clusdf[fn] = relative_entropies

    return clusdf


def baseline_entropy(data, normalize=False):
    """
    Compute the feature entropy of the baseline (unclustered, entire dataset).
    @param data: Baseline dataset
    @type data: pd.DataFrame
    @param normalize: If true, normalize the entropy values by the maximum possible entropy H_max = np.log(num_values)
    @type normalize: bool
    @return: Baseline entropy values for each feature
    @rtype: pd.DataFrame
    """

    # Result dataframe (1 row)
    base_entr = pd.DataFrame(0, index=np.arange(1), columns=data.columns.drop(['out', 'class', 'cluster']))

    # Iterate over features (columns)
    for fn in base_entr.columns:
        grouped = data.groupby(fn)
        Px = grouped.size() / len(data)

        # Compute entropy and optionally normalize it
        base_entr[fn] = - (Px * np.log(Px)).sum()
        if normalize:
            base_entr[fn] = base_entr[fn] / grouped.ngroups
    return base_entr



def select_cluster_entropy(entropy, c, threshold=None):
    """
    Select the feature entropy of one cluster and apply the given threshold.
    @param entropy:
    @type entropy:
    @param c: Cluster to select
    @type c: int
    @param threshold: Maximum entropy
    @type threshold: float
    @return: Thresholded entropy of the chosen cluster
    @rtype: pd.Series
    """
    # Select feature entropy for cluster c
    e = entropy.iloc[[c]]

    # If threshold is set, remove features with entropy >= threshold
    if threshold is not None:
        e = e.applymap(lambda z: z if z < threshold else np.nan)
        e = e.dropna(axis='columns')
    return e


def compute_cluster_groups_rate(data, clustering, entropy, baseline, threshold=0.5, max_rate=0.75):
    rate = entropy.div(baseline.iloc[0], axis='columns')
    data['cluster'] = clustering

    # Iterate over groupby cluster column
    groups = []
    for c, cluster in data.groupby('cluster'):

        # Cluster feature entropy
        e = select_cluster_entropy(entropy, c, threshold)
        e = e.mask(rate >= max_rate).dropna(axis=1)

        # Iterate over columns (that were not dropped)
        group = {}
        for i, col in enumerate(e.columns):
            counts = cluster.value_counts(subset=col, normalize=True, sort=False)
            group[col] = counts.idxmax()

        groups = groups + [group]
    return pd.DataFrame(groups)


def cluster_groups(data, entropy, threshold=0.65):
    """
    Detect the subgroups indicated by the clustering of data.
    Search for dominant features using the feature entropy per cluster.
    @param data: Data with clustering labels (column 'cluster')
    @type data: pd.DataFrame
    @param entropy: Feature entropy per cluster (one row per cluster, features are columns)
    @type entropy: pd.DataFrame
    @param threshold: Maximal entropy value
    @type threshold: float
    @return: Detected subgroups
    @rtype: pd.DataFrame
    """
    # Iterate over groupby cluster column
    groups = []
    for c, cluster in data.groupby('cluster'):

        if c < 0:
            continue

        # Select entropy for cluster c
        e = select_cluster_entropy(entropy, c, threshold)

        # Iterate over columns
        group = {}
        for i, col in enumerate(e.columns):
            counts = cluster.value_counts(subset=col, normalize=True, sort=False)
            group[col] = counts.idxmax()
        groups = groups + [group]

    return pd.DataFrame(groups)


def normalized_entropy_groups(data, threshold=0.65):
    """
    Detect subgroups for the clustered data by using the normalized entropy.
    @param data: Clustered data (column 'cluster' contains cluster labels)
    @type data: pd.DataFrame
    @param threshold: Maximum entropy
    @type threshold: float
    @return: Detected subgroups from clusters
    @rtype: pd.DataFrame
    """
    # NE = normalized_entropy(data)
    NE = normalized_entropy_cluster(data)
    return cluster_groups(data, NE, threshold)





def visualize_value_counts(data, clustering, entropy, c=0, threshold=None, normalize=True):
    """
    Visualize the value frequencies/counts for all features of a cluster of the dataset.
    @param data: Dataset
    @type data: pd.DataFrame
    @param clustering: Clustering labels (cluster numbers)
    @type clustering: list of int
    @param entropy: Feature entropy per cluster
    @type entropy: pd.DataFrame
    @param c: Label of the cluster to visualize
    @type c: int
    @param threshold: Maximum entropy per feature. If None, no thresholding is applied.
    @type threshold: float or None
    @param normalize: If True, plot relative frequencies of the values; otherwise plot absolute frequencies.
    @type normalize: bool
    @return: Subgroup described by this cluster (optionally thresholded)
    @rtype: dict of (str, obj)
    """
    # Get feature entropy for cluster c (thresholded)
    e = select_cluster_entropy(entropy, c, threshold)

    # Create subplots
    fig = plt.figure(figsize=(25, 5))
    gs = fig.add_gridspec(1, len(e.columns))
    ax = gs.subplots()  # sharey=True)

    # Group data by cluster column --> get cluster c
    data_label = util.label_data(data, clustering)
    grouped = data_label.groupby('cluster')
    cdata = grouped.get_group(c)

    # Plot value counts for selected columns
    group = {}
    for i, col in enumerate(e.columns):
        col_type = cdata.dtypes[col]
        counts = cdata.value_counts(subset=col, normalize=normalize, sort=False)

        # Plot bars for relative value frequency
        counts.plot.bar(ax=ax[i])
        ax[i].set_title(
            f"entropy={e[col].iloc[0]:.4f},\n")

        # Get most frequent value for this feature
        group[col] = counts.idxmax()

    # Finalize figure
    repr_group = ", ".join(str(x) + "=" + str(y) for x, y in group.items())
    fig.suptitle(f"Represented group: {repr_group}", fontsize='xx-large', y=1.1)  # y to have title above other text
    plt.show()

    return group


def slider_value_count(data, clustering, entropy, threshold_enabled=True):
    """
    Return an interactive visualization (ipywidget) of the value counts for the clustered data.
    @param data: Data (without clustering label), shape = m features x n rows
    @type data: pd.DataFrame
    @param clustering: Clustering labels (length n)
    @type clustering: list of int
    @param entropy: Feature entropy per cluster
    @type entropy: pd.DataFrame
    @param threshold_enabled: If set to true, add a slider for maximum entropy threshold
    @type threshold_enabled: bool
    """
    if threshold_enabled:
        interact(lambda c, t: visualize_value_counts(data, clustering, entropy, c, t),
                 c=(0, clustering.max()),
                 t=(0.1, entropy.max().max() + 0.1)
                 )
    else:
        interact(lambda c: visualize_value_counts(data, entropy, c),
                 c=(0, clustering.max()))
    return


def boxplot_entropy(entropy, baseline=None):
    """
    Plot a boxplot for the feature entropy over all clusters
    @param entropy: Feature entropy values for all clusters
    @type entropy: pd.DataFrame
    @param baseline: Feature entropy values for the entire dataset (without clustering)
    @type baseline: pd.DataFrame or pd.Series
    """
    fig = plt.figure(figsize=(20, 5))
    ax = fig.add_subplot(111)

    # Legend
    cols = entropy.columns
    colors = sb.color_palette(n_colors=len(cols))
    patches = [Patch(color=c) for c, _ in zip(colors, cols)]
    leg_labels = [f'{idx}: {fn}' for idx, fn in enumerate(cols, start=1)]
    fig.legend(patches, leg_labels)

    # Boxplot
    box = ax.boxplot(entropy, patch_artist=True)
    for p, c in zip(box['boxes'], colors):
        p.set_color(c)
    for p in box['medians']:
        p.set_color('black')

    # Plot baseline entropy
    if baseline is not None:
        offset = 0.5
        line_width = 1
        thickness = 3
        plotX = np.arange(len(cols))  # + offset

        # Define and plot lines (as collection of line segments)
        lines = [[(x + offset, y), (x + offset + line_width, y)] for x, y in enumerate(baseline.values[0])]
        lc = LineCollection(lines, colors=colors, linewidths=thickness)
        ax.add_collection(lc)

    return

