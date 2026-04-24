import io
import msoffcrypto
import pandas as pd
from typing import Any

def load_password_excel(uploaded_file: Any, password: str) -> pd.DataFrame:
    # Create a buffer for the decrypted file
    decrypted_buffer = io.BytesIO()

    # Open the encrypted file
    office_file = msoffcrypto.OfficeFile(uploaded_file)
    office_file.load_key(password=password)
    office_file.decrypt(decrypted_buffer)

    df = pd.read_excel(decrypted_buffer)
    return df
