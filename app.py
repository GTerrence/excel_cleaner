from datetime import datetime

import msoffcrypto
import pandas as pd
import streamlit as st

from excel_cleaner.utils import clean_mandiri, create_zip, load_password_excel, remove_rows, style_rows_red
from excel_cleaner.validators import ColumnFilledRule, ValidationRule, mark_rows

MANDIRI_RULES: list[ValidationRule] = [
    ColumnFilledRule(column_name='Debit'),
]

st.set_page_config(page_title="Excel Cleaner", page_icon="📝")


def main() -> None:
    st.title("Excel Cleaner")

    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    if uploaded_file is not None:
        # Check if file is encrypted
        is_encrypted = False
        try:
            office_file = msoffcrypto.OfficeFile(uploaded_file)
            is_encrypted = office_file.is_encrypted()
        except Exception:
            # If it's not an msoffcrypto file, it's likely not encrypted
            pass

        uploaded_file.seek(0)  # Reset buffer position

        password = ""
        if is_encrypted:
            password = st.text_input("File is password protected. Enter password:", type="password")
            if not password:
                st.warning("Please enter a password to proceed.")
                return

        if st.button("Process File"):
            with st.spinner("Processing file..."):
                try:
                    if is_encrypted:
                        df = load_password_excel(uploaded_file, password)
                    else:
                        df = pd.read_excel(uploaded_file)

                    # Pre-processing
                    clean_df = clean_mandiri(df)
                    if 'Saldo' in clean_df.columns:
                        clean_df.drop(columns=['Saldo'], inplace=True)

                    # Validation rules masking
                    mask = mark_rows(clean_df, MANDIRI_RULES)

                    # Apply styles and row removal
                    cleaned_df = remove_rows(clean_df, mask)
                    styled_styler = style_rows_red(clean_df, mask)

                    # Create ZIP file
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    zip_data = create_zip(cleaned_df, styled_styler, date_str)

                    st.success("File processed successfully!")

                    st.download_button(
                        label="Download Reports (ZIP)",
                        data=zip_data,
                        file_name=f"Mandiri_Reports_{date_str}.zip",
                        mime="application/zip",
                    )

                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")


if __name__ == "__main__":
    main()
