# Path: modules/date_utils.py
# This file is responsible for parsing and translating dates, converting them to a unified format.
# It also converts relative dates (e.g., "2 дня назад", "3 часа назад") to absolute dates.

from datetime import datetime, timedelta
import re

# Dictionary for translating Cyrillic month names to Latin
MONTHS_TRANSLATION = {
    'янв': 'Jan', 'февр': 'Feb', 'мар': 'Mar', 'апр': 'Apr', 'май': 'May', 'июн': 'Jun',
    'июл': 'Jul', 'авг': 'Aug', 'сент': 'Sep', 'окт': 'Oct', 'нояб': 'Nov', 'дек': 'Dec',
    'фев': 'Feb', 'марта': 'Mar', 'апреля': 'Apr', 'мая': 'May', 'июня': 'Jun', 'июля': 'Jul',
    'августа': 'Aug', 'сентября': 'Sep', 'октября': 'Oct', 'ноября': 'Nov', 'декабря': 'Dec'
}

def translate_month(date_str):
    """
    Translate Cyrillic month names to Latin.

    Args:
        date_str (str): Date string containing Cyrillic month names.

    Returns:
        str: Date string with Latin month names.
    """
    for ru, en in MONTHS_TRANSLATION.items():
        date_str = re.sub(r'\b{}\b'.format(ru), en, date_str, flags=re.IGNORECASE)
    return date_str

def parse_date(date_str):
    """
    Parse a date string into a datetime object, handling both absolute and relative date formats.

    Args:
        date_str (str): Date string to parse, either in absolute format (e.g., "10 сентября 2023") 
                        or relative format (e.g., "2 дня назад").

    Returns:
        datetime: Parsed datetime object or None if parsing fails.
    """
    # Translate Cyrillic month names to Latin
    date_str = translate_month(date_str)

    # Defined date formats
    formats = [
        '%d %b %Y',          # e.g., 10 Sep 2023
        '%d %b. %Y\u202fг.',  # e.g., 10 Sep. 2023 г.
        '%d %b. %Y',          # e.g., 10 Sep. 2023
        '%d %b %Y\u202fг.',   # e.g., 10 Sep 2023 г.
        '%Y-%m-%d'            # e.g., 2023-09-10
    ]
    
    # Try to parse the date using predefined formats
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Handle relative dates (e.g., "2 дня назад", "3 часа назад")
    relative_date_patterns = [
        (re.compile(r'(\d+)\s+дней?\s+назад'), timedelta(days=1)),
        (re.compile(r'(\d+)\s+дня?\s+назад'), timedelta(days=1)),
        (re.compile(r'(\d+)\s+часов?\s+назад'), timedelta(hours=1)),
        (re.compile(r'(\d+)\s+часа?\s+назад'), timedelta(hours=1)),
        (re.compile(r'(\d+)\s+минут?\s+назад'), timedelta(minutes=1)),
        (re.compile(r'(\d+)\s+минуты?\s+назад'), timedelta(minutes=1))
    ]
    
    for pattern, delta in relative_date_patterns:
        match = pattern.search(date_str)
        if match:
            value = int(match.group(1))
            return datetime.now() - (value * delta)
    
    # If no matching format, return None
    return None
