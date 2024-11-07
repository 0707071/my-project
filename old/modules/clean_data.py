import pandas as pd
from fuzzywuzzy import fuzz

def clean_data(input_filename, output_filename, similarity_threshold=80, verbose=False):
    """
    Clean data by removing strict and non-strict duplicates.

    Args:
        input_filename (str): Path to the input CSV file.
        output_filename (str): Path to the output CSV file.
        similarity_threshold (int): Similarity threshold for fuzzy matching (default is 70).
        verbose (bool): Flag to enable/disable verbose output.

    Returns:
        tuple: Number of rows before and after cleaning.
    """
    print("Начало функции clean_data")
    print(f"Загрузка данных из файла {input_filename}...")
    try:
        df = pd.read_csv(input_filename)
        print(f"Данные успешно загружены. Количество строк: {len(df)}")
    except Exception as e:
        print(f"Ошибка при загрузке данных: {str(e)}")
        raise

    rows_before = len(df)

    # Stage 1: "Strict" comparison and removal of exact duplicates
    print("Удаление строгих дубликатов...")
    df_no_strict_duplicates = df.drop_duplicates(subset=['title', 'description']).reset_index(drop=True)
    print(f"Строгих дубликатов удалено: {len(df) - len(df_no_strict_duplicates)}")

    # Stage 2: Preparation for "non-strict" comparison
    print("Подготовка данных для 'нестрогого' сравнения...")
    df_no_strict_duplicates_sorted = df_no_strict_duplicates.sort_values('title').reset_index()

    # List of row indices to remove
    indexes_to_remove = set()

    print("Поиск дубликатов с 'нестрогим' сравнением...")
    # Use fuzzy matching algorithm to find duplicates
    for i in range(len(df_no_strict_duplicates_sorted) - 1):
        for j in range(i + 1, len(df_no_strict_duplicates_sorted)):
            # Use fuzz.token_sort_ratio to compare strings
            similarity_title = fuzz.token_sort_ratio(df_no_strict_duplicates_sorted.loc[i, 'title'], df_no_strict_duplicates_sorted.loc[j, 'title'])
            similarity_text = fuzz.token_sort_ratio(df_no_strict_duplicates_sorted.loc[i, 'description'], df_no_strict_duplicates_sorted.loc[j, 'description'])

            # if similarity_title > similarity_threshold or similarity_text > similarity_threshold:
            if similarity_text > similarity_threshold:
                indexes_to_remove.add(df_no_strict_duplicates_sorted.loc[j, 'index'])  # Add index to set for removal
                if verbose:
                    print(f"Найден дубликат: строка {i + 1} и строка {j + 1}")
                    print(f"Схожесть заголовка: {similarity_title}, Схожесть текста: {similarity_text}")

    # Remove duplicates found in the 'non-strict' comparison stage
    df_final = df_no_strict_duplicates_sorted.drop(df_no_strict_duplicates_sorted[df_no_strict_duplicates_sorted['index'].isin(indexes_to_remove)].index).reset_index(drop=True)

    print("Сохранение данных...")
    # Save cleaned data back to CSV
    df_final.to_csv(output_filename, index=False)

    rows_after = len(df_final)

    # Output information about the number of removed and remaining rows
    print(f"Строк удалено на этапе 'нестрогого' сравнения: {len(indexes_to_remove)}")
    print(f"Оставшиеся строки после очистки: {rows_after}")
    print(f"Данные очищены и сохранены в '{output_filename}'.")

    print("Конец функции clean_data")
    return rows_before, rows_after