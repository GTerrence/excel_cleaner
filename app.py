from datetime import datetime

import msoffcrypto
import streamlit as st

from excel_cleaner.constants import BankType
from excel_cleaner.utils import (
    create_zip,
    get_cleaned_df,
    get_dataframe,
    remove_rows,
    style_rows_red,
)
from excel_cleaner.validators import ValidationRule, load_rules_config, mark_rows

RULES: dict[BankType, list[ValidationRule]] = load_rules_config()

st.set_page_config(page_title="Excel Cleaner", page_icon="📝")


def main() -> None:
    st.title("Excel Cleaner")

    bank_type = st.selectbox("Bank Type", BankType)
    uploaded_file = st.file_uploader("Upload Excel or CSV File", type=["xlsx", "xls", "csv"])

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
                    df = get_dataframe(uploaded_file, bank_type, password)

                    # Pre-processing
                    clean_df = get_cleaned_df(df, bank_type)

                    # Validation rules masking
                    mask = mark_rows(clean_df, RULES[bank_type])

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
                        file_name=f"{bank_type}_Reports_{date_str}.zip",
                        mime="application/zip",
                    )

                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")


if __name__ == "__main__":
    main()
