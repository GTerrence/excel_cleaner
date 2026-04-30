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
        # Change data locally to test substring match
        df_test = self.df.copy()
        df_test['C'] = ['green apple', 'banana', 'cherry', 'fresh date']
        
        rule = ColumnContainsRule('C', ['apple', 'date'])
        mask = rule.apply(df_test)
        self.assertEqual(mask.tolist(), [True, False, False, True])

    def test_mark_rows_combined(self):
        df_test = self.df.copy()
        df_test['C'] = ['green apple', 'yellow banana', 'cherry', 'fresh date']
        rules = [
            ColumnFilledRule('A'),
            ColumnContainsRule('C', ['banana'])
        ]
        # 'foo' matches filled
        # '' matches nothing but 'yellow banana' matches C
        # None matches nothing
        # 'bar' matches filled
        mask = mark_rows(df_test, rules)
        self.assertEqual(mask.tolist(), [1, 1, 0, 1])

if __name__ == '__main__':
    # run_manual_test()
    unittest.main()
