import pandas as pd
import asyncio
import csv
import os
import logging
from modules.fetch_data import fetch_xmlstock_search_results, process_search_results
from modules.utils import clean_domain

MAX_CONCURRENT_REQUESTS = 20  # Максимальное количество одновременно выполняемых запросов
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )

async def fetch_company_data(input_file, output_file, config):
    try:
        # Пробуем загрузить данные из входного файла
        try:
            df = pd.read_excel(input_file, engine='openpyxl')
            logging.info(f"Успешно загружено {len(df)} строк из Excel файла.")
        except Exception:
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
                logging.info(f"Успешно загружено {len(df)} строк из CSV файла с кодировкой utf-8.")
            except Exception:
                df = pd.read_csv(input_file, encoding='latin1')
                logging.info(f"Успешно загружено {len(df)} строк из CSV файла с кодировкой latin1.")
        
        logging.info(f"Колонки входного файла: {df.columns.tolist()}")
    except Exception as e:
        logging.error(f"Ошибка при чтении входного файла: {str(e)}")
        return

    search_column = config['search_column']
    search_queries = config['search_queries']
    use_domain = config.get('use_domain', False)
    company_name_column = config['company_name_column']

    # Проверка наличия необходимых колонок
    required_columns = [company_name_column, search_column, 'Organization description']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logging.error(f"В входном файле отсутствуют следующие колонки: {', '.join(missing_columns)}")
        raise ValueError(f"В входном файле отсутствуют необходимые колонки: {', '.join(missing_columns)}")

    results = []

    # Функция для сохранения результатов
    def save_results(results, output_file, mode='w'):
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_file, mode=mode, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
        logging.info(f"Данные сохранены в файл {output_file}")

    # Асинхронная функция для обработки компании
    async def process_company(index, row):
        company_name = row[company_name_column]
        search_value = row[search_column]

        if pd.isna(search_value):
            logging.info(f"Пропуск компании '{company_name}': отсутствует значение для поиска.")
            return []

        if use_domain:
            search_value = clean_domain(str(search_value))
            search_prefix = f"site:{search_value}"
        else:
            search_prefix = str(search_value)

        company_results = []

        for query in search_queries:
            full_query = f"{search_prefix} {query}"
            logging.info(f"Выполняется запрос для компании '{company_name}': '{full_query}'")

            async with semaphore:
                search_results = await fetch_xmlstock_search_results(full_query, "", "", config)
                if search_results:
                    logging.info(f"Результаты запроса: {search_results}")
                else:
                    logging.info(f"Запрос не дал результатов для: {full_query}")

                if search_results:
                    articles = await process_search_results(search_results)
                    if articles:
                        article = articles[0]  # Берем только первый результат для каждого запроса
                        result = row.to_dict()
                        result.update({
                            'company_name': company_name,
                            'search_query': full_query,
                            'title': article.get('title', ''),
                            'link': article.get('article_url', ''),
                            'found_text': article.get('text', '')[:1000],
                            'description': article.get('text', '')[:5000]
                        })
                        company_results.append(result)
                        logging.info(f"Результаты для компании '{company_name}': {result}")
                        break

            await asyncio.sleep(config.get('delay_between_queries', 1))

        if not company_results:
            result = row.to_dict()
            result.update({
                'company_name': company_name,
                'search_query': '',
                'title': '',
                'link': '',
                'found_text': '',
                'description': ''
            })
            company_results.append(result)

        return company_results

    # Обработка компаний асинхронно
    tasks = [process_company(index, row) for index, row in df.iterrows()]
    for task_batch in asyncio.as_completed(tasks, timeout=60):
        try:
            company_results = await task_batch
            results.extend(company_results)

            # Сохраняем промежуточные результаты
            if len(results) >= 10:
                save_results(results, output_file, mode='a')
                results.clear()
        except asyncio.TimeoutError:
            logging.error(f"Таймаут для одной из компаний")

    # Сохранение оставшихся результатов
    if results:
        save_results(results, output_file, mode='a')

    logging.info(f"Обработка завершена.")

def run_fetch_company_data(input_file, output_file, config):
    setup_logging()
    asyncio.run(fetch_company_data(input_file, output_file, config))
