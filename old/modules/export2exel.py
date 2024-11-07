import pandas as pd
import ast

def process_analysis(analysis_str):
    try:
        # Очищаем строку и преобразуем её в список
        cleaned_str = analysis_str.strip().strip('"""').strip('```python').strip('```')
        
        # Попытка конвертации очищенной строки в список
        analysis_list = ast.literal_eval(cleaned_str)

        # Логируем результат преобразования
        print(f"Преобразованный список: {analysis_list}")

        # Проверка на вложенные списки и обработка их
        def clean_element(element):
            if isinstance(element, list):
                return ', '.join(map(str, element)) if element else "N/A"
            return element

        # Обрабатываем список с учетом вложенных элементов и пустых значений
        analysis_list = [clean_element(item) for item in analysis_list]

        # Убедимся, что список всегда содержит 8 элементов
        while len(analysis_list) < 8:
            analysis_list.append("NA")

        return analysis_list[:8]  # Возвращаем только первые 8 элементов
    except Exception as e:
        # Логируем возможную ошибку и возвращаем пустые значения
        print(f"Ошибка при обработке анализа: {str(e)}")
        return ["NA"] * 8

# Загрузка данных из CSV
df = pd.read_csv('results/Avant_Tecno_Oy/2024-10-24/search_results_analysed.csv')

# Применение функции к столбцу 'analysis' и разложение на отдельные столбцы
df[['Company Name', 'Potential', 'Sales Notes', 'Description', 'Revenue', 'Country', 'Website', 'Assumed Website']] = df['analysis'].apply(process_analysis).apply(pd.Series)

# Сохранение обновленного DataFrame в новый CSV файл
df.to_csv('results/Avant_Tecno_Oy/2024-10-24/Avant_Tecno_Oy.csv', index=False)