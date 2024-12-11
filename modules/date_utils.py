# Path: modules/date_utils.py
from datetime import datetime, timedelta
import re
import pytz

# Расширенный словарь для перевода месяцев
MONTHS_TRANSLATION = {
    'янв': 'Jan', 'февр': 'Feb', 'мар': 'Mar', 'апр': 'Apr', 'май': 'May', 'июн': 'Jun',
    'июл': 'Jul', 'авг': 'Aug', 'сент': 'Sep', 'окт': 'Oct', 'нояб': 'Nov', 'дек': 'Dec',
    'января': 'Jan', 'февраля': 'Feb', 'марта': 'Mar', 'апреля': 'Apr', 'мая': 'May', 'июня': 'Jun',
    'июля': 'Jul', 'августа': 'Aug', 'сентября': 'Sep', 'октября': 'Oct', 'ноября': 'Nov', 'декабря': 'Dec',
    'фев': 'Feb', 'сен': 'Sep'
}

# Словарь для относительных дат
RELATIVE_TIME = {
    'сегодня': lambda: datetime.now(),
    'вчера': lambda: datetime.now() - timedelta(days=1),
    'позавчера': lambda: datetime.now() - timedelta(days=2),
    'неделю назад': lambda: datetime.now() - timedelta(weeks=1),
    'месяц назад': lambda: datetime.now() - timedelta(days=30),
    'год назад': lambda: datetime.now() - timedelta(days=365),
}

# Паттерны для относительных дат
RELATIVE_PATTERNS = {
    r'(\d+)\s*(?:минут[уы]?|мин\.?)\s*назад': ('minutes', 1),
    r'(\d+)\s*(?:час[ао]в?|ч\.?)\s*назад': ('hours', 1),
    r'(\d+)\s*(?:дн[яей]|день|дн\.?)\s*назад': ('days', 1),
    r'(\d+)\s*(?:недел[иь]|нед\.?)\s*назад': ('weeks', 1),
    r'(\d+)\s*(?:месяц(?:ев|а)?|мес\.?)\s*назад': ('days', 30),
    r'(\d+)\s*(?:год[а]?|лет|г\.?)\s*назад': ('days', 365),
}

def translate_month(date_str):
    """Переводит русские названия месяцев на английский."""
    if not date_str:
        return date_str
    
    result = date_str.lower()
    for ru, en in MONTHS_TRANSLATION.items():
        result = re.sub(r'\b{}\b'.format(ru), en, result, flags=re.IGNORECASE)
    return result

def parse_date(date_str):
    """
    Парсит строку с датой в datetime объект.
    
    Args:
        date_str (str): Строка с датой в любом формате
        
    Returns:
        datetime: Объект datetime или None если парсинг не удался
    """
    if not date_str or not isinstance(date_str, str):
        return None
        
    date_str = date_str.lower().strip()
    
    # 1. Проверяем точные совпадения
    if date_str in RELATIVE_TIME:
        return RELATIVE_TIME[date_str]()
    
    # 2. Проверяем относительные даты
    for pattern, (unit, multiplier) in RELATIVE_PATTERNS.items():
        match = re.search(pattern, date_str)
        if match:
            try:
                value = int(match.group(1)) * multiplier
                return datetime.now() - timedelta(**{unit: value})
            except (ValueError, TypeError):
                continue
    
    # 3. Переводим месяцы и пробуем разные форматы
    translated = translate_month(date_str)
    formats = [
        '%d %b %Y',           # 31 Dec 2023
        '%d.%m.%Y',           # 31.12.2023
        '%Y-%m-%d',           # 2023-12-31
        '%d/%m/%Y',           # 31/12/2023
        '%d %B %Y',           # 31 December 2023
        '%d %b %Y %H:%M',     # 31 Dec 2023 15:30
        '%Y-%m-%d %H:%M:%S',  # 2023-12-31 15:30:45
        '%d.%m.%Y %H:%M',     # 31.12.2023 15:30
        '%d %b',              # 31 Dec (текущий год)
        '%d.%m',              # 31.12 (текущий год)
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(translated, fmt)
            # Если в формате нет года, добавляем текущий
            if '%Y' not in fmt:
                current_year = datetime.now().year
                parsed = parsed.replace(year=current_year)
            return parsed
        except ValueError:
            continue
    
    return None

def format_date(dt, output_format='%Y-%m-%d %H:%M:%S'):
    """
    Форматирует datetime объект в строку.
    
    Args:
        dt (datetime): Объект datetime для форматирования
        output_format (str): Желаемый формат вывода
        
    Returns:
        str: Отформатированная строка с датой или None
    """
    if not dt:
        return None
    try:
        return dt.strftime(output_format)
    except (ValueError, AttributeError):
        return None
