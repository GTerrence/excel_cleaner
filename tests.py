import re
import unittest

import pandas as pd

from utils import remove_rows, style_rows_red
from validators import ColumnContainsRule, ColumnFilledRule, mark_rows


class TestValidators(unittest.TestCase):
    def setUp(self) -> None:
        self.df = pd.DataFrame(
            {'A': ['foo', '', None, 'bar'], 'B': [1, 2, 3, 4], 'C': ['apple', 'banana', 'cherry', 'date']}
        )

    def test_column_filled_rule(self) -> None:
        rule = ColumnFilledRule('A')
        mask = rule.apply(self.df)
        # Expected: True for 'foo' and 'bar', False for '' and None
        self.assertEqual(mask.tolist(), [True, False, False, True])

    def test_column_contains_rule(self) -> None:
        # Change data locally to test substring match
        df_test = self.df.copy()
        df_test['C'] = ['green apple', 'banana', 'cherry', 'fresh date']

        rule = ColumnContainsRule('C', ['apple', 'date'])
        mask = rule.apply(df_test)
        self.assertEqual(mask.tolist(), [True, False, False, True])

    def test_mark_rows_combined(self) -> None:
        df_test = self.df.copy()
        df_test['C'] = ['green apple', 'yellow banana', 'cherry', 'fresh date']
        rules = [ColumnFilledRule('A'), ColumnContainsRule('C', ['banana'])]
        # 'foo' matches filled
        # '' matches nothing but 'yellow banana' matches C
        # None matches nothing
        # 'bar' matches filled
        mask = mark_rows(df_test, rules)
        self.assertEqual(mask.tolist(), [1, 1, 0, 1])


class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        self.df = pd.DataFrame({'A': ['foo', 'bar', 'baz'], 'B': [1, 2, 3]})
        self.mask = pd.Series([True, False, True])

    def test_remove_rows(self) -> None:
        result_df = remove_rows(self.df, self.mask)
        # Should keep only the middle row where mask is False
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df.iloc[0]['A'], 'bar')
        self.assertEqual(result_df.iloc[0]['B'], 2)

    def test_style_rows_red(self) -> None:
        styler = style_rows_red(self.df, self.mask)

        self.assertIsInstance(styler, pd.io.formats.style.Styler)

        # Verify the style by checking the HTML representation
        html = styler.to_html()

        # Extract the CSS block that defines the red background
        match = re.search(r'(.*?)\{\s*background-color:\s*red;\s*\}', html)
        self.assertIsNotNone(match)

        css_selectors = match.group(1)  # type: ignore[union-attr]
        # Check that rows 0 and 2 are targeted by the red style
        self.assertIn('row0', css_selectors)
        self.assertIn('row2', css_selectors)
        # Ensure row 1 is NOT styled red
        self.assertNotIn('row1', css_selectors)


if __name__ == '__main__':
    unittest.main()
