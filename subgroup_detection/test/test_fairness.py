import unittest
import pandas as pd
from subgroup_detection import fairness

X = pd.DataFrame({
    'out':   [0,0,0,0,1,1,1,1],
    'class': [0,0,1,1,1,1,1,0],
    'A': ['w','w','b','b','h','h','h','b']
})

# P:    5     N:    3
# PP:   4     PN:   4
# TP:   3     FP:   1
# TN:   2     FN:   2

# Cluster 0: P=0, N=2, TP=0, FP=0, TN=2, FN=0
# Cluster 1: P=3, N=0, TP=1, FP=0, TN=0, FN=2
# Cluster 2: P=2, N=1, TP=2, FP=1, TN=0, FN=0

# Group A=w: P=0, N=2, TP=0, FP=0, TN=2, FN=0
# Group A=b: P=2, N=1, TP=0, FP=1, TN=0, FN=2
# Group A=h: P=3, N=0, TP=3, FP=0, TN=0, FN=0

L = [0,0,1,1,1,2,2,2]


G = pd.DataFrame({
    'A': ['w', 'b', 'h'],
    #'B': ['o', 'o', 'y']
})


class MyTestCase(unittest.TestCase):
    def test_cluster_fairness(self):
        # TODO adapt FairnessResult
        general, subgroup, priv_groups = fairness.cluster_fairness(X, L, G, pos_label=0)

        print(subgroup.c_eq_opp)
        print(subgroup.g_eq_opp)

        # Check isinstance and shapes
        self.assertIsInstance(general, pd.DataFrame)
        self.assertIsInstance(subgroup, pd.DataFrame)
        self.assertIsInstance(priv_groups, dict)
        self.assertEqual(general.shape, (2, 5))         # 2 rows (class 0/1) x 5 metrics
        self.assertEqual(subgroup.shape, (3, 8))        # num_cluster x 6
        self.assertEqual(len(priv_groups), 3)           # one priv group per cluster

        # General metrics
        self.assertAlmostEqual(general.base_rate.iloc[0], 3 / 8)
        self.assertAlmostEqual(general.base_rate.iloc[1], 5 / 8)
        self.assertAlmostEqual(general.sensitivity.iloc[0], 2 / (2 + 1))
        self.assertAlmostEqual(general.sensitivity.iloc[1], 3 / (3 + 2))
        self.assertAlmostEqual(general.specificity.iloc[0], 3 / (3 + 2))
        self.assertAlmostEqual(general.specificity.iloc[1], 2 / (2 + 1))
        self.assertEqual(general.accuracy.iloc[0], general.accuracy.iloc[1])
        self.assertAlmostEqual(general.accuracy.iloc[0], 5 / 8)
        self.assertAlmostEqual(general.f1_score.iloc[0], 2 * (3 / 4) * (3 / 5) / (3 / 4 + 3 / 5))

        # Cluster/subgroup fairness
        # Cluster 0
        self.assertEqual(priv_groups[0], {'A': 'w'})
        self.assertAlmostEqual(subgroup.c_stat_par.iloc[0], 0 / 2 - 4 / 6)
        # self.assertAlmostEqual(subgroup.c_eq_opp.iloc[0], 3 / 5 - 0)    # TPR=0 (0 pos ex)
        self.assertAlmostEqual(subgroup.c_avg_odds.iloc[0], ((0 / 2 - 1 / 1) + (0 - 3 / 5)) / 2)  # TPR=0 (0 pos ex)
        self.assertAlmostEqual(subgroup.c_acc.iloc[0], 2 / 2)
        self.assertAlmostEqual(subgroup.g_stat_par.iloc[0], 0 / 2 - 4 / 6)
        # self.assertAlmostEqual(subgroup.g_eq_opp.iloc[0], 3 / 5 - 0)    #TPR=0 (0 pos ex)
        self.assertAlmostEqual(subgroup.g_avg_odds.iloc[0], ((0 / 2 - 1 / 1) + (0 - 3 / 5)) / 2) # TPR=0 (0 pos ex)
        self.assertAlmostEqual(subgroup.g_acc.iloc[0], 2 / 2)

        # Cluster 1
        self.assertAlmostEqual(priv_groups[1], {'A': 'b'})
        self.assertAlmostEqual(subgroup.c_stat_par.iloc[1], 1 / 3 - 3 / 5)
        self.assertAlmostEqual(subgroup.c_eq_opp.iloc[1], 1 - 1 / 3)
        self.assertAlmostEqual(subgroup.c_avg_odds.iloc[1], ((1 - 1 / 3) + (1 / 3 - 2 / 2)) / 2)    # FPR=1 (0 neg ex)
        self.assertAlmostEqual(subgroup.c_acc.iloc[1], 1 / 3)
        self.assertAlmostEqual(subgroup.g_stat_par.iloc[1], 1 / 3 - 3 / 5)
        self.assertAlmostEqual(subgroup.g_eq_opp.iloc[1], 1 - 0)
        self.assertAlmostEqual(subgroup.g_avg_odds.iloc[1], ((1 / 1 - 0 / 2) + (0 / 2 - 3 / 3)) / 2)
        self.assertAlmostEqual(subgroup.g_acc.iloc[1], 0 / 3)

        # Cluster 2
        self.assertAlmostEqual(priv_groups[2], {'A': 'h'})
        self.assertAlmostEqual(subgroup.c_stat_par.iloc[2], 3 / 3 - 1 / 5)
        # self.assertAlmostEqual(subgroup.c_eq_opp.iloc[2], 1 / 3 - 2 / 2)
        self.assertAlmostEqual(subgroup.c_avg_odds.iloc[2], ((1 / 1 - 0 / 2) + (2 / 2 - 1 / 3)) / 2)
        self.assertAlmostEqual(subgroup.c_acc.iloc[2], 2 / 3)
        self.assertAlmostEqual(subgroup.g_stat_par.iloc[2], 3 / 3 - 1 / 5)
        # self.assertAlmostEqual(subgroup.g_eq_opp.iloc[2], 0 / 2 - 3 / 3)
        self.assertAlmostEqual(subgroup.g_avg_odds.iloc[2], ((1 - 1 / 3) + (3 / 3 - 0 / 2)) / 2) # FPR=1 (0 neg ex)
        self.assertAlmostEqual(subgroup.g_acc.iloc[2], 3 / 3)


if __name__ == '__main__':
    unittest.main()
