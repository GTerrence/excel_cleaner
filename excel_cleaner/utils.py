import io
import zipfile
from datetime import datetime
from typing import Any

import msoffcrypto
import pandas as pd

from .constants import BankType


def load_password_excel(uploaded_file: Any, password: str) -> pd.DataFrame:
    # Create a buffer for the decrypted file
    decrypted_buffer = io.BytesIO()

    # Open the encrypted file
    office_file = msoffcrypto.OfficeFile(uploaded_file)
    office_file.load_key(password=password)
    office_file.decrypt(decrypted_buffer)

    df = pd.read_excel(decrypted_buffer)
    return df


def remove_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(how='all')


def remove_empty_cols(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(axis=1, how='all')


def remove_rows(df: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    """
    Remove rows from the DataFrame where the boolean mask is True.
    """
    return df[~mask].copy()


def style_rows_red(df: pd.DataFrame, mask: pd.Series) -> 'pd.io.formats.style.Styler':
    """
    Style the rows of a DataFrame to red based on a boolean mask.
    The mask should be True for rows that need to be styled.
    """

    def highlight_rows(x: pd.DataFrame) -> pd.DataFrame:
        df_style = pd.DataFrame('', index=x.index, columns=x.columns)
        df_style.loc[mask, :] = 'background-color: red'
        return df_style

    return df.style.apply(highlight_rows, axis=None)


def create_zip(cleaned_df: pd.DataFrame, styled_styler: 'pd.io.formats.style.Styler', date_str: str, bank_type: BankType) -> bytes:
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Save cleaned file
        cleaned_buffer = io.BytesIO()
        cleaned_df.to_excel(cleaned_buffer, index=False, engine='openpyxl')
        zip_file.writestr(f"{bank_type}_{date_str}_cleaned.xlsx", cleaned_buffer.getvalue())

        # Save validation file
        validation_buffer = io.BytesIO()
        styled_styler.to_excel(validation_buffer, index=False, engine='openpyxl')
        zip_file.writestr(f"{bank_type}_{date_str}_validation.xlsx", validation_buffer.getvalue())

    return zip_buffer.getvalue()


def clean_mandiri(df: pd.DataFrame) -> pd.DataFrame:
    # NOTE: Find index for row with value "No"
    header_idx = df[df.iloc[:, 1] == 'No'].index[0]
    footer_idx = df[df.iloc[:, df.columns.get_loc("Unnamed: 19")] == 'Mandiri Call 14000'].index[0]
    clean_df = df.iloc[header_idx:footer_idx].copy()

    clean_df = remove_empty_rows(clean_df)
    clean_df = remove_empty_cols(clean_df)

    # NOTE: Rename column 'e-Statement' to 'No.'
    clean_df.loc[2:, 'Unnamed: 1'] = clean_df.loc[2:, 'e-Statement'].astype(str)
    clean_df.drop(columns=['e-Statement'], inplace=True)
    clean_df.rename(
        columns={
            'Unnamed: 1': 'No.',
            'Unnamed: 4': 'Tanggal',
            'Unnamed: 7': 'Description',
            'Unnamed: 15': 'Kredit',
            'Unnamed: 18': 'Debit',
            'Unnamed: 21': 'Saldo',
        },
        inplace=True,
    )

    # NOTE: Merge multiple rows that should be in one row.
    clean_df['No.'] = clean_df['No.'].ffill()

    def smart_append(series: pd.Series) -> str:
        # Filter out empty/NaN values, convert to string, and join with a space
        valid_items = [str(item).strip() for item in series if pd.notna(item) and str(item).strip() != ""]
        return " ".join(valid_items).replace("\n", " ")

    clean_df = clean_df.groupby('No.', as_index=False).agg(smart_append)

    # Sort numerically by "No." column
    clean_df['sort_key'] = pd.to_numeric(clean_df['No.'], errors='coerce')
    clean_df = clean_df.sort_values('sort_key').drop(columns=['sort_key']).reset_index(drop=True)

    # Reformat date
    clean_df['Tanggal'] = clean_df['Tanggal'].apply(reformat_date_string)
    clean_df['Kredit'] = clean_df['Kredit'].apply(convert_to_money_format)
    clean_df['Debit'] = clean_df['Debit'].apply(convert_to_money_format)

    # NOTE:Drop unneccessary column
    clean_df.drop(columns=['Saldo'], inplace=True)

    return clean_df


def clean_bca(df: pd.DataFrame) -> pd.DataFrame:
    clean_df = df.rename(columns={'Unnamed: 4': 'Type'})

    # NOTE: Drop footer
    clean_df = clean_df.dropna(subset=['Type'])

    # NOTE:Drop unneccessary column
    clean_df.drop(columns=['Balance', 'Branch'], inplace=True)
    return clean_df


def get_dataframe(file: Any, bank_type: BankType, password: str | None = None) -> pd.DataFrame:
    match bank_type:
        case BankType.BCA:
            kwargs = {'skiprows': 4}
        case _:
            kwargs = {}

    if file.type == 'text/csv':
        df = pd.read_csv(file, **kwargs)
    elif password:
        df = load_password_excel(file, password)
    else:
        df = pd.read_excel(file, **kwargs)

    return df


def get_cleaned_df(df: pd.DataFrame, bank_type: BankType) -> pd.DataFrame:
    match bank_type:
        case BankType.MANDIRI:
            return clean_mandiri(df)
        case BankType.BCA:
            return clean_bca(df)
        case _:
            raise NotImplementedError(f'Bank type "{bank_type}" is not implemented yet.')


def reformat_date_string(
    date_str: str,
    input_format: str = "%d %b %Y %H:%M:%S WIB",
    output_format: str = "%d/%m/%Y"
) -> str:
    """
    Removes the time component of a date string based on input and output formats.
    Using datetime instead of regex makes it robust to format changes.
    """
    dt = datetime.strptime(date_str, input_format)
    return dt.strftime(output_format)

def convert_to_money_format(value: float | int | str) -> str:
    """
    Format a number to Indonesian Rupiah (Rp) money format.
    Uses '.' as the thousand separator and removes trailing commas/decimals.
    """
    if pd.isna(value) or value == '':
        return '0'

    try:
        if isinstance(value, str):
            value = value.replace(',', '')

        num = int(float(value))
        return f"{num:,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(value)
