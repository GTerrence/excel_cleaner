import os
from pprint import pprint

from dotenv import load_dotenv

from utils import clean_mandiri, load_password_excel, remove_rows, style_rows_red
from validators import ColumnContainsRule, ColumnFilledRule, mark_rows

load_dotenv()

MANDIRI_RULES = [
    ColumnFilledRule('Debit'),
    # ColumnContainsRule('Description', ['Transfer dari BANK MANDIRI']),
]

def run_manual_test():
    filename = 'local/sample_mandiri2.xlsx'
    password = os.getenv('TEST_PASSWORD', '')

    with open(filename, 'rb') as f:
        df = load_password_excel(f, password)
        clean_df = clean_mandiri(df)
        clean_df.drop(columns=['Saldo'], inplace=True)
        mask = mark_rows(clean_df, MANDIRI_RULES)
        
        # Test the style_rows_red function
        styled_df = style_rows_red(clean_df, mask)
        
        # Save the result to a real excel file
        output_filename = 'local/test_styled_output.xlsx'
        styled_df.to_excel(output_filename, engine='openpyxl', index=False)
        print(f"File successfully saved to {output_filename}")


if __name__ == '__main__':
    run_manual_test()
