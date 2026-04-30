import unittest
import pandas as pd
from validators import ColumnFilledRule, ColumnContainsRule, mark_rows

class TestValidators(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'A': ['foo', '', None, 'bar'],
            'B': [1, 2, 3, 4],
            'C': ['apple', 'banana', 'cherry', 'date']
        })

    def test_column_filled_rule(self):
        rule = ColumnFilledRule('A')
        mask = rule.apply(self.df)
        # Expected: True for 'foo' and 'bar', False for '' and None
        self.assertEqual(mask.tolist(), [True, False, False, True])

    def test_column_contains_rule(self):
        rule = ColumnContainsRule('C', ['apple', 'date'])
        mask = rule.apply(self.df)
        self.assertEqual(mask.tolist(), [True, False, False, True])

    def test_mark_rows_combined(self):
        rules = [
            ColumnFilledRule('A'),
            ColumnContainsRule('C', ['banana'])
        ]
        # 'foo' matches filled
        # '' matches nothing but 'banana' matches C
        # None matches nothing
        # 'bar' matches filled
        mask = mark_rows(self.df, rules)
        self.assertEqual(mask.tolist(), [1, 1, 0, 1])

if __name__ == '__main__':
    # run_manual_test()
    unittest.main()
