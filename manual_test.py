import os
from pprint import pprint

from dotenv import load_dotenv

from utils import clean_mandiri, load_password_excel

load_dotenv()


def run_manual_test():
    filename = 'local/sample_mandiri2.xlsx'
    password = os.getenv('TEST_PASSWORD', '')

    with open(filename, 'rb') as f:
        df = load_password_excel(f, password)
        clean_df = clean_mandiri(df)
        pprint(clean_df.head(n=20).to_dict(orient='records'))


if __name__ == '__main__':
    run_manual_test()
