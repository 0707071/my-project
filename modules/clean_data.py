# Path: modules/clean_data.py
# This file is responsible for cleaning the data by removing strict and non-strict duplicates.

import pandas as pd
from fuzzywuzzy import fuzz
import logging


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Очищает данные от дубликатов и некачественного контента
    """
    try:
        initial_rows = len(df)
        
        # Удаление дубликатов
        df_clean = df.drop_duplicates(subset=['link'])
        print(f"Removed {initial_rows - len(df_clean)} duplicate URLs")
        
        df_clean = df_clean.drop_duplicates(subset=['description'])
        print(f"Removed {len(df) - len(df_clean)} duplicate contents")
        
        # Более мягкая фильтрация подозрительного контента
        suspicious_patterns = [
            'page not found',
            'access denied',
            'subscription required',
            'please subscribe'
        ]
        pattern = '|'.join(suspicious_patterns)
        mask = ~df_clean['description'].str.lower().str.contains(pattern, na=False)
        df_clean = df_clean[mask]
        
        return df_clean
    except Exception as e:
        logging.error(f"Error cleaning data: {str(e)}")
        return df  # Возвращаем исходный датафрейм в случае ошибки
