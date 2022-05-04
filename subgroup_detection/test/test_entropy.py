import unittest
import numpy as np
import pandas as pd
from subgroup_detection import entropy

df = pd.DataFrame({
    'col1': ['a', 'b', 'b', 'c', 'b', 'c', 'a'],
    'col2': [0, 1, 2, 3, 3, 4, 5],
    'cluster': [-1, 0, 0, 0, 0, 1, 1]
})


class MyTestCase(unittest.TestCase):
    def test_normalized_entropy(self):
        E = entropy.normalized_entropy(df)
        self.assertIsInstance(E, pd.DataFrame)
        self.assertEqual(E.shape, (2, 2))

        # Check col1
        H_max = np.log(3)
        self.assertEqual(E.col1.iloc[0], - (0.75 * np.log(0.75) + 0.25 * np.log(0.25)) / H_max)
        self.assertEqual(E.col1.iloc[1], - (0.5 * np.log(0.5) + 0.5 * np.log(0.5)) / H_max)

        # Check col2
        H_max = np.log(6)
        self.assertEqual(E.col2.iloc[0], - (0.25 * np.log(0.25) + 0.25 * np.log(0.25) + 0.5 * np.log(0.5)) / H_max)
        self.assertEqual(E.col2.iloc[1], - (0.5 * np.log(0.5) + 0.5 * np.log(0.5)) / H_max)

    def test_relative_entropy(self):
        E = entropy.relative_entropy(df)
        self.assertIsInstance(E, pd.DataFrame)
        self.assertEqual(E.shape, (2, 2))

        # Check col1
        self.assertEqual(E.col1.iloc[0], 0.75 * np.log(0.75 / (3 / 7)) + 0.25 * np.log(0.25 / (2 / 7)))
        self.assertEqual(E.col1.iloc[1], 0.5 * np.log(0.5 / (2 / 7)) + 0.5 * np.log(0.5 / (2 / 7)))

        # Check col2
        self.assertEqual(E.col2.iloc[0],
                         0.25 * np.log(0.25 / (1 / 7)) + 0.25 * np.log(0.25 / (1 / 7)) + 0.5 * np.log(0.5 / (2 / 7)))
        self.assertEqual(E.col2.iloc[1], 0.5 * np.log(0.5 / (1/7)) + 0.5 * np.log(0.5 / (1/7)))

    def test_normalized_entropy_cluster(self):
        NEC = entropy.normalized_entropy_cluster(df)
        self.assertIsInstance(NEC, pd.DataFrame)
        self.assertEqual(NEC.shape, (2, 2))

        # Check col1
        self.assertEqual(NEC.col1.iloc[0], - (0.75 * np.log(0.75) + 0.25 * np.log(0.25)) / np.log(2))
        self.assertEqual(NEC.col1.iloc[1], - (0.5 * np.log(0.5) + 0.5 * np.log(0.5)) / np.log(2))

        # Check col2
        self.assertEqual(NEC.col2.iloc[0], - (0.25 * np.log(0.25) + 0.25 * np.log(0.25) + 0.5 * np.log(0.5)) / np.log(3))
        self.assertEqual(NEC.col2.iloc[1], - (0.5 * np.log(0.5) + 0.5 * np.log(0.5)) / np.log(2))

    def test_cluster_groups_normalized(self):
        NE = entropy.normalized_entropy(df)

        G = entropy.cluster_groups(df, NE, threshold=0.5)
        self.assertEqual(G.shape, (2, 1))
        self.assertEqual(G.columns, ['col2'])
        self.assertTrue(np.isnan(G.col2.iloc[0]))
        self.assertEqual(G.col2.iloc[1], 4)

        G = entropy.cluster_groups(df, NE, 0)
        self.assertEqual(G.shape, (2,0))

        G = entropy.cluster_groups(df, NE, 0.6)
        self.assertEqual(G.shape, (2, 2))
        self.assertListEqual(G.columns.tolist(), ['col1', 'col2'])
        self.assertEqual(G.col1.iloc[0], 'b')
        self.assertEqual(G.col2.iloc[0], 3)
        self.assertTrue(np.isnan(G.col1.iloc[1]))
        self.assertEqual(G.col2.iloc[1], 4)

    def test_cluster_groups_relative(self):
        RE = entropy.relative_entropy(df)
        print(RE)

        G = entropy.cluster_groups(df, RE, threshold=0.5)
        self.assertEqual(G.shape, (2, 1))
        self.assertEqual(G.columns, ['col1'])
        self.assertEqual(G.col1.iloc[0], 'b')
        self.assertTrue(np.isnan(G.col1.iloc[1]))

        G = entropy.cluster_groups(df, RE, 0)
        self.assertEqual(G.shape, (2, 0))

        G = entropy.cluster_groups(df, RE, 0.6)
        self.assertEqual(G.shape, (2, 2))
        self.assertListEqual(G.columns.tolist(), ['col1', 'col2'])
        self.assertEqual(G.col1.iloc[0], 'b')
        self.assertEqual(G.col2.iloc[0], 3)
        self.assertEqual(G.col1.iloc[1], 'a')
        self.assertTrue(np.isnan(G.col2.iloc[1]))

if __name__ == '__main__':
    unittest.main()
