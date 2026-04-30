from abc import ABC, abstractmethod
from typing import List, Any
import pandas as pd
import re

class ValidationRule(ABC):
    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.Series:
        """
        Evaluate the DataFrame and return a boolean Series indicating which rows match the rule.
        """
        pass

class ColumnFilledRule(ValidationRule):
    def __init__(self, column_name: str):
        self.column_name = column_name

    def apply(self, df: pd.DataFrame) -> pd.Series:
        if self.column_name not in df.columns:
            return pd.Series(False, index=df.index)

        # Consider a row filled if it is not NA and not an empty string
        mask = df[self.column_name].notna()
        # Ensure it's treated as string before checking for empty string, only if it's object/string type
        if pd.api.types.is_string_dtype(df[self.column_name]) or pd.api.types.is_object_dtype(df[self.column_name]):
            mask = mask & (df[self.column_name].astype(str).str.strip() != '')

        return mask

class ColumnContainsRule(ValidationRule):
    def __init__(self, column_name: str, target_values: List[Any]):
        self.column_name = column_name
        self.target_values = target_values

    def apply(self, df: pd.DataFrame) -> pd.Series:
        if self.column_name not in df.columns:
            return pd.Series(False, index=df.index)

        # Escape the target values to avoid invalid regex, then join with OR (|)
        str_targets = [str(t) for t in self.target_values]
        pattern = '|'.join(re.escape(t) for t in str_targets)

        col_str = df[self.column_name].astype(str)
        return col_str.str.contains(pattern, case=False, regex=True, na=False)

def mark_rows(df: pd.DataFrame, rules: List[ValidationRule]) -> pd.Series:
    """
    Marks rows in the DataFrame that match any of the provided ValidationRules.

    Args:
        df: The pandas DataFrame to evaluate.
        rules: A list of ValidationRule instances.

    Returns:
        A pandas Series of integers (1 for marked, 0 for unmarked) with the same index as the input DataFrame.
    """
    if df.empty or not rules:
        return pd.Series(0, index=df.index)

    # Initialize a mask of all False
    combined_mask = pd.Series(False, index=df.index)

    # Apply logical OR across all rules
    for rule in rules:
        combined_mask = combined_mask | rule.apply(df)

    # Convert boolean mask to 1s and 0s
    return combined_mask.astype(int)
