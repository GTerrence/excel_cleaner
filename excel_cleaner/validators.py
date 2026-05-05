import re
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
import streamlit as st

from .constants import BankType


class ValidationRule(ABC):
    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.Series:
        """
        Evaluate the DataFrame and return a boolean Series indicating which rows match the rule.
        """
        raise NotImplementedError


class ColumnFilledRule(ValidationRule):
    def __init__(self, column_name: str) -> None:
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
    def __init__(self, column_name: str, target_values: list[Any]) -> None:
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

class ColumnEqualsRule(ValidationRule):
    def __init__(self, column_name: str, target_values: list[Any]) -> None:
        self.column_name = column_name
        self.target_values = target_values

    def apply(self, df: pd.DataFrame) -> pd.Series:
        if self.column_name not in df.columns:
            return pd.Series(False, index=df.index)

        str_targets = [str(t).lower() for t in self.target_values]
        col_str = df[self.column_name].astype(str).str.lower()
        return col_str.isin(str_targets)


def mark_rows(df: pd.DataFrame, rules: list[ValidationRule]) -> pd.Series:
    """
    Marks rows in the DataFrame that match any of the provided ValidationRules.

    Args:
        df: The pandas DataFrame to evaluate.
        rules: A list of ValidationRule instances.

    Returns:
        A pandas Series of boolean (True for marked, False for unmarked) with the same index as the input DataFrame.
    """
    if df.empty or not rules:
        return pd.Series(False, index=df.index)

    # Initialize a mask of all False
    combined_mask = pd.Series(False, index=df.index)

    # Apply logical OR across all rules
    for rule in rules:
        combined_mask = combined_mask | rule.apply(df)

    # Convert boolean mask to 1s and 0s
    return combined_mask.astype(bool)


VALIDATION_RULES_CLASS_REGISTRY = {
    "ColumnFilledRule": ColumnFilledRule,
    "ColumnContainsRule": ColumnContainsRule,
    "ColumnEqualsRule": ColumnEqualsRule,
}


def load_rules_config() -> dict[BankType, list[ValidationRule]]:
    validation_rule_config = st.secrets.get('VALIDATION_RULE', {})

    validation_rules: dict[BankType, list[ValidationRule]] = {}
    for bank_type, rules in validation_rule_config.items():
        bank_type = BankType(bank_type)
        rules_list = []
        for rule in rules:
            rule_class = VALIDATION_RULES_CLASS_REGISTRY[rule["class"]]
            rules_list.append(rule_class(**rule["params"]))
        validation_rules[bank_type] = rules_list

    return validation_rules
