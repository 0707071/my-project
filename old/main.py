import os
import json
import argparse
import asyncio
from datetime import datetime
import pandas as pd
import ast
from modules.fetch_data import fetch_and_save_articles
from modules.clean_data import clean_data
from modules.analyse_data import run_analyse_data  # Используем run_analyse_data для анализа
from modules.client_management import get_client_and_date
from modules.utils import load_config

def load_search_queries(roles_dir):
    """Загрузка поисковых запросов из search_query.json."""
    with open(os.path.join(roles_dir, 'search_query.json'), 'r') as f:
        search_queries = json.load(f)
    queries = search_queries['queries']
    include = search_queries['include']
    exclude = search_queries['exclude']
    return queries, include, exclude

def process_analysis(analysis_str):
    """Обработка строки анализа данных."""
    try:
        analysis_list = ast.literal_eval(analysis_str)
        if len(analysis_list) >= 6:
            return analysis_list[0], analysis_list[1], analysis_list[2], analysis_list[3], analysis_list[4], analysis_list[5]
        else:
            return analysis_list[0] if len(analysis_list) > 0 else "", \
                   analysis_list[1] if len(analysis_list) > 1 else 0, \
                   analysis_list[2] if len(analysis_list) > 2 else "", \
                   analysis_list[3] if len(analysis_list) > 3 else [], \
                   analysis_list[4] if len(analysis_list) > 4 else "", \
                   analysis_list[5] if len(analysis_list) > 5 else ""
    except:
        return "", 0, "", [], "", ""

async def export_to_excel(input_file, output_file):
    """Экспорт данных в Excel."""
    print(f"Экспорт данных в Excel...")
    df = pd.read_csv(input_file)
    df[['Company', 'Signal Strength', 'Time Frame', 'Key Phrases', 'Sales Team Notes', 'News Summary']] = df['analysis'].apply(process_analysis).apply(pd.Series)
    df.to_excel(output_file, index=False)
    print(f"Данные успешно экспортированы в {output_file}")

async def fetch_data(client_name, config, queries, include, exclude, verbose, continue_from=None):
    """Асинхронно получает данные из API xmlstock и парсит статьи."""
    print("Начинаем получение и обработку данных...")
    search_date_str = datetime.now().strftime('%Y-%m-%d')
    current_search_dir = os.path.join('results', client_name, search_date_str)
    os.makedirs(current_search_dir, exist_ok=True)
    results_file = os.path.join(current_search_dir, 'search_results.csv')

    start_index = 0
    if continue_from:
        start_index = queries.index(continue_from)
        print(f"Продолжаем с запроса: {continue_from}")

    for query in queries[start_index:]:
        print(f"Получаем данные для запроса: {query}")
        await fetch_and_save_articles(query, include, exclude, config, results_file, verbose)
        await asyncio.sleep(2)  # Небольшая задержка между запросами

    if os.path.exists(results_file) and os.path.getsize(results_file) > 0:
        df = pd.read_csv(results_file)
        print(f"Всего получено статей: {len(df)}")
        return True
    else:
        print("Статьи не были получены. Файл результатов не был создан или пуст.")
        return False

async def main_async():
    """Асинхронная основная функция программы."""
    parser = argparse.ArgumentParser(description="Signal Enricher")
    parser.add_argument('--fetch', action='store_true', help="Только получение данных")
    parser.add_argument('--clean', action='store_true', help="Только очистка данных")
    parser.add_argument('--analyze', action='store_true', help="Только анализ данных")
    parser.add_argument('--continue_from', action='store_true', help="Продолжить с последнего обработанного запроса")
    args = parser.parse_args()

    try:
        client_name, search_date = get_client_and_date()
        if client_name is None:
            return

        print(f"Клиент: {client_name}, Дата: {search_date}")

        search_date_str = search_date.strftime('%Y-%m-%d')

        roles_dir = os.path.join('results', client_name, 'roles')
        queries, include, exclude = load_search_queries(roles_dir)

        config = load_config('config/search_config.json')
        verbose = config.get('verbose', False)
        
        if config.get('exclude_pdf', False):
            exclude += " -filetype:pdf"

        continue_from = None
        if args.continue_from:
            last_processed_query = input("Введите последний обработанный запрос: ")
            continue_from = next((q for q in queries if q.startswith(last_processed_query)), None)
            if continue_from:
                print(f"Продолжаем с запроса: {continue_from}")
            else:
                print("Запрос не найден. Начинаем с начала.")

        data_fetched = False
        if args.fetch or not (args.clean or args.analyze):
            data_fetched = await fetch_data(client_name, config, queries, include, exclude, verbose, continue_from)
        
        file_path = os.path.join('results', client_name, search_date_str, 'search_results.csv')
        if (args.clean or not (args.fetch or args.analyze)) and (data_fetched or os.path.exists(file_path)):
            print("Начинаем очистку данных...")
            output_file = os.path.join('results', client_name, search_date_str, 'search_results_cleaned.csv')
            
            if os.path.getsize(file_path) > 0:
                try:
                    rows_before, rows_after = clean_data(file_path, output_file, verbose=True)
                    print(f"Очистка данных завершена. Было строк: {rows_before}, стало строк: {rows_after}")
                    print(f"Удалено дубликатов: {rows_before - rows_after}")
                except Exception as e:
                    print(f"Ошибка при очистке данных: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"Предупреждение: Входной файл {file_path} пуст. Очистка данных не выполнена.")
        elif not data_fetched:
            print("Пропускаем этап очистки, так как данные не были получены.")
        
        cleaned_file = os.path.join('results', client_name, search_date_str, 'search_results_cleaned.csv')
        analysed_file = os.path.join('results', client_name, search_date_str, 'search_results_analysed.csv')
        if (args.analyze or not (args.fetch or args.clean)) and (data_fetched or os.path.exists(cleaned_file)):
            print("Начинаем анализ данных...")
            await run_analyse_data(cleaned_file, analysed_file, roles_dir, config)
            print("Анализ данных завершен.")
            
            # Экспорт в Excel
            excel_file = os.path.join('results', client_name, search_date_str, f"{client_name}_{search_date_str}.xlsx")
            await export_to_excel(analysed_file, excel_file)
        elif not data_fetched:
            print("Пропускаем этап анализа, так как данные не были получены.")

        print("Программа успешно завершена.")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Wrapper для запуска асинхронной main функции."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
