# Path: modules/clean_data.py
# This file is responsible for cleaning the data by removing strict and non-strict duplicates.

import pandas as pd
from fuzzywuzzy import fuzz
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import re
from app.websockets import send_task_log


def clean_data(df: pd.DataFrame, task_id: Optional[int] = None) -> pd.DataFrame:
    """
    Очищает данные от дубликатов и применяет базовую обработку.
    Теперь с поддержкой отслеживания прогресса.
    """
    total_steps = 5  # Общее количество шагов очистки
    current_step = 0
    
    if task_id:
        send_task_log(task_id, "Starting data cleaning", 'clean', 33, 0)
    
    # 1. Удаляем дубликаты
    current_step += 1
    initial_rows = len(df)
    df = df.drop_duplicates(subset=['title', 'description'], keep='first')
    if task_id:
        removed = initial_rows - len(df)
        progress = (current_step / total_steps) * 100
        send_task_log(
            task_id, 
            f"Removed {removed} duplicate entries", 
            'clean',
            33 + progress // 3,
            progress
        )
    
    # 2. Очищаем текст
    current_step += 1
    if task_id:
        progress = (current_step / total_steps) * 100
        send_task_log(
            task_id, 
            "Cleaning text content", 
            'clean',
            33 + progress // 3,
            progress
        )
    
    df['title'] = df['title'].apply(lambda x: clean_text(x) if pd.notna(x) else x)
    df['description'] = df['description'].apply(lambda x: clean_text(x) if pd.notna(x) else x)
    
    # 3. Нормализуем даты
    current_step += 1
    if task_id:
        progress = (current_step / total_steps) * 100
        send_task_log(
            task_id, 
            "Normalizing dates", 
            'clean',
            33 + progress // 3,
            progress
        )
    
    if 'date' in df.columns:
        df['date'] = df['date'].apply(parse_date)
    
    # 4. Удаляем пустые строки
    current_step += 1
    initial_rows = len(df)
    df = df.dropna(subset=['description'])
    if task_id:
        removed = initial_rows - len(df)
        progress = (current_step / total_steps) * 100
        send_task_log(
            task_id, 
            f"Removed {removed} empty entries", 
            'clean',
            33 + progress // 3,
            progress
        )
    
    # 5. Финальная проверка
    current_step += 1
    if task_id:
        progress = 100  # Последний шаг
        send_task_log(
            task_id, 
            f"Cleaning completed. Final dataset: {len(df)} entries", 
            'clean',
            66,  # Этап очистки завершен
            progress
        )
    
    return df

def clean_text(text: str) -> str:
    """Очищает текст от лишних пробелов и специальных символов"""
    if pd.isna(text):
        return text
        
    # Заменяем множественные пробелы и переносы строк на одиночные
    text = re.sub(r'\s+', ' ', str(text))
    # Убираем пробелы в начале и конце
    text = text.strip()
    return text

def parse_date(date_str: str) -> Optional[datetime]:
    """Парсит дату из строки"""
    if pd.isna(date_str):
        return None
        
    try:
        return pd.to_datetime(date_str)
    except:
        return None
