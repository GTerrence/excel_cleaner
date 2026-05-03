# Excel Cleaner

Excel Cleaner is a Streamlit-based web application designed to automate the cleaning and validation of bank transaction exports. It processes Excel files, applies specific validation rules based on the selected bank type, and generates a downloadable ZIP archive containing both the cleaned data and a styled report highlighting the removed entries.

## Features

- **Bank-Specific Processing**: Supports applying different validation rules depending on the selected bank type.
- **Encrypted File Support**: Automatically detects password-protected Excel files and prompts for decryption without saving the unencrypted file to disk.
- **Automated Data Cleaning**: Pre-processes data and drops unnecessary columns.
- **Validation Rules**: Uses predefined rules to mark and remove invalid or unnecessary rows dynamically.
- **Styled Reporting**: Generates a styled Excel sheet where removed rows are highlighted in red for easy auditing.
- **ZIP Export**: Packages the cleaned data and the styled report into a single convenient ZIP download.

## Prerequisites

- Python 3.12+

## Installation

1. Clone this repository or download the source code.
2. Ensure you have a virtual environment set up outside or inside the project, e.g.:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Start the Streamlit application by running:
```bash
streamlit run app.py
```

1. Select your **Bank Type** from the dropdown menu.
2. Upload your Excel `.xlsx` or `.xls` file.
3. If the file is encrypted, enter the password when prompted.
4. Click **Process File**.
5. Once processing is complete, click **Download Reports (ZIP)** to retrieve the cleaned data and styled report.

## Development

This project uses `ruff` for linting/formatting and `mypy` for static type checking. Configuration is maintained in `pyproject.toml`.

To check code style and formatting:
```bash
ruff check .
ruff format .
```

To run type checks:
```bash
mypy .
```
