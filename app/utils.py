import pandas as pd
from io import StringIO, BytesIO

def csv_to_excel_in_memory(csv_data, selected_columns=None):
    """
    Преобразует CSV в формат Excel в памяти.
    
    Args:
        csv_data: CSV данные в виде строки или BytesIO/StringIO
        selected_columns: Список колонок для включения (опционально)
        
    Returns:
        BytesIO: Excel файл в памяти
    """
    # Если входные данные - строка, преобразуем в StringIO
    if isinstance(csv_data, str):
        csv_data = StringIO(csv_data)
    
    # Если входные данные - поток байтов, конвертируем в StringIO
    if isinstance(csv_data, BytesIO):
        csv_data = StringIO(csv_data.getvalue().decode('utf-8-sig'))
    
    # Читаем CSV
    df = pd.read_csv(csv_data)
    
    # Фильтруем колонки если нужно
    if selected_columns and all(col in df.columns for col in selected_columns):
        df = df[selected_columns]
    
    # Создаем Excel в памяти
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
    
    excel_buffer.seek(0)
    return excel_buffer 