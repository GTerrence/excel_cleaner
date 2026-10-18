import re
import unittest

import pandas as pd

from excel_cleaner.constants import BankType
from excel_cleaner.utils import StatementSummary, append_summary, get_summary, remove_rows, style_rows_red
from excel_cleaner.validators import ColumnContainsRule, ColumnEqualsRule, ColumnFilledRule, mark_rows


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

    def test_column_equals_rule(self) -> None:
        df_test = self.df.copy()
        df_test['C'] = ['green apple', 'Banana', 'cherry', 'date']

        rule = ColumnEqualsRule('C', ['green apple', 'banana'])
        mask = rule.apply(df_test)
        self.assertEqual(mask.tolist(), [True, True, False, False])

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


class TestSummary(unittest.TestCase):
    def test_append_summary(self) -> None:
        df = pd.DataFrame(
            {
                'Date': ['01/02/2026', '02/02/2026'],
                'Description': ['foo', 'bar'],
                'Amount': ['100', '200'],
                'Type': ['CR', 'DB'],
            }
        )
        summary = StatementSummary(
            starting_balance='7.998.519',
            total_credit='88.612.240',
            total_debit='85.467.039',
            ending_balance='11.143.720',
        )

        result = append_summary(df, summary)

        # Original rows are kept, four summary rows are appended.
        self.assertEqual(len(result), 6)
        self.assertEqual(result.iloc[:2].reset_index(drop=True).equals(df), True)

        expected = ['Starting Balance', 'Total Credit', 'Total Debit', 'Ending Balance']
        self.assertEqual(result['Date'].iloc[2:].tolist(), expected)
        self.assertEqual(result['Type'].iloc[2:].tolist(), ['7.998.519', '88.612.240', '85.467.039', '11.143.720'])
        # Middle columns are left empty.
        self.assertEqual(result['Description'].iloc[2:].tolist(), ['', '', '', ''])

    def test_get_summary_bca(self) -> None:
        df = pd.DataFrame(
            {
                'Date': ['01/02/2026', 'Starting Balance', 'Credit', 'Debet', 'Ending Balance'],
                'Description': ['trx', '=', '=', '=', '='],
                'Branch': ['0000', '7998519.52', '88612240.37', '85467039.67', '11143720.22'],
                'Amount': ['100', None, None, None, None],
                'Unnamed: 4': ['CR', None, None, None, None],
            }
        )

        summary = get_summary(df, BankType.BCA)

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.starting_balance, '7.998.519')
        self.assertEqual(summary.total_credit, '88.612.240')
        self.assertEqual(summary.total_debit, '85.467.039')
        self.assertEqual(summary.ending_balance, '11.143.720')

    def test_get_summary_mandiri(self) -> None:
        df = pd.DataFrame(
            [
                {'label': 'Saldo Awal/Initial Balance', 'value': '1.370.753,91'},
                {'label': 'Dana Masuk/Incoming Transactions', 'value': '81.971.635,00'},
                {'label': 'Dana Keluar/Outgoing Transactions', 'value': '82.160.428,00'},
                {'label': 'Saldo Akhir/Closing Balance', 'value': '1.181.960,91'},
            ]
        )

        summary = get_summary(df, BankType.MANDIRI)

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.starting_balance, '1.370.753')
        self.assertEqual(summary.total_credit, '81.971.635')
        self.assertEqual(summary.total_debit, '82.160.428')
        self.assertEqual(summary.ending_balance, '1.181.960')

    def test_get_summary_uob(self) -> None:
        rows = [
            ['01 Agustus', '01 Agustus', 'BALANCE B/F', '', '', '', '589'],
            ['02 Agustus', '02 Agustus', 'BI FAST CREDIT', '', '', '19,200,000', '19,200,589'],
            ['31 Agustus', '31 Agustus', 'Pajak', '156', '', '6,062'],
            ['', '', 'Total', '291,410,311', '291,415,784', '6,062'],
        ]

        summary = get_summary((rows, '2026'), BankType.UOB)

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.starting_balance, '589')
        self.assertEqual(summary.total_credit, '291.415.784')
        self.assertEqual(summary.total_debit, '291.410.311')
        self.assertEqual(summary.ending_balance, '6.062')


if __name__ == '__main__':
    unittest.main()
