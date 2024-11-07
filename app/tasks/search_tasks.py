from app import celery, db
from app.models.task import SearchTask
from app.models.search_query import SearchQuery
from app.models.search_result import SearchResult
from app.models.prompt import Prompt
from app.websockets import send_task_log
from datetime import datetime, timedelta
import os
import sys
import pandas as pd
import asyncio
import json
import shutil
from dotenv import load_dotenv
import re
from llm_clients import get_llm_client
import logging

# Добавляем путь к модулям поиска
sys.path.append(os.path.join(os.path.dirname(__file__), '../../modules'))

from fetch_data import fetch_xmlstock_search_results, fetch_and_parse, process_search_results
from clean_data import clean_data
from analyse_data import run_analyse_data

# Загружаем переменные окружения
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

async def analyze_with_retry(text, prompt):
    max_attempts = 3
    llm_client = get_llm_client(
        model_name="gpt-4o",
        config={
            'max_retries': max_attempts,
            'api_keys': os.getenv('OPENAI_API_KEYS', '').split(',')
        }
    )
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text}
    ]
    
    try:
        return await llm_client.get_completion(messages)
    except Exception as e:
        print(f"Error with LLM client: {str(e)}")
        raise

def parse_relative_date(date_str):
    """Преобразует относительную дату в абсолютную"""
    if not date_str or pd.isna(date_str):
        return None
        
    # Словарь для русских слов
    ru_dict = {
        'дней': 'days',
        'дня': 'days',
        'день': 'days',
        'часов': 'hours',
        'часа': 'hours',
        'час': 'hours',
        'минут': 'minutes',
        'минуты': 'minutes',
        'минута': 'minutes'
    }
    
    try:
        # Если это уже datetime или валидная строка даты
        return pd.to_datetime(date_str)
    except:
        # Обрабатываем относиельные даты
        for ru, en in ru_dict.items():
            if ru in str(date_str).lower():
                number = int(re.findall(r'\d+', str(date_str))[0])
                delta = {en: number}
                return datetime.now() - timedelta(**delta)
        return None

@celery.task(bind=True)
def run_search(self, task_id):
    """Асинхронная задача для выполнения поиска и анализа"""
    async def async_search():
        search_task = SearchTask.query.get(task_id)
        if not search_task:
            return {'status': 'failed', 'error': 'Task not found'}
        
        try:
            # Получаем параметры поиска из БД
            search_query = SearchQuery.query.get(search_task.search_query_id)
            if not search_query:
                raise ValueError("Search query not found")

            # Получаем активный промпт
            prompt = Prompt.query.filter_by(
                client_id=search_task.client_id,
                is_active=True
            ).first()
            if not prompt:
                raise ValueError("No active prompt found")

            # Создаем директории для результатов
            search_dir = os.path.join('results', str(search_task.client_id))
            os.makedirs(search_dir, exist_ok=True)

            # Пути к файлам результатов
            raw_results = os.path.join(search_dir, 'search_results.csv')
            cleaned_results = os.path.join(search_dir, 'search_results_cleaned.csv')
            analyzed_results = os.path.join(search_dir, 'search_results_analyzed.csv')
            formatted_results = os.path.join(search_dir, f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

            # 1. Поиск и сохранение статей
            for query in search_query.main_phrases.split('\n'):
                if not query.strip():
                    continue
                    
                try:
                    search_results = await fetch_xmlstock_search_results(
                        query.strip(),
                        search_query.include_words,
                        search_query.exclude_words,
                        {
                            'days': search_query.days_back,
                            'results_per_page': search_query.results_per_page,
                            'num_pages': search_query.num_pages
                        },
                        verbose=True
                    )
                    
                    if search_results:
                        articles = await process_search_results(search_results)
                        if articles:
                            df = pd.DataFrame(articles)
                            if os.path.exists(raw_results):
                                df.to_csv(raw_results, mode='a', header=False, index=False)
                            else:
                                df.to_csv(raw_results, index=False)
                except Exception as e:
                    logging.error(f"Error fetching articles for query '{query}': {str(e)}")
                    continue

            if not os.path.exists(raw_results) or os.path.getsize(raw_results) == 0:
                raise ValueError("No search results found for any query")

            # 2. Очистка данных
            df = pd.read_csv(raw_results)
            df_cleaned = clean_data(df)
            df_cleaned.to_csv(cleaned_results, index=False)

            # 3. Анализ данных с промптом из БД
            await run_analyse_data(
                cleaned_results, 
                analyzed_results,
                prompt.content,  # Передаем сам промпт вместо пути к файлу
                {
                    'model': 'gpt-4o-mini',
                    'api_keys': os.getenv('OPENAI_API_KEYS', '').split(','),
                    'max_retries': 3
                }
            )

            # 4. Форматирование результатов
            if os.path.exists(analyzed_results):
                results_df = pd.read_csv(analyzed_results)
                
                # Получаем названия колонок из промпта в БД
                column_names = [name.strip() for name in (prompt.column_names or '').split('\n') if name.strip()]
                
                # Разбираем ответы модели
                for idx, row in results_df.iterrows():
                    try:
                        analysis = eval(row['analysis'])
                        for col_name, value in zip(column_names, analysis):
                            results_df.at[idx, col_name] = value
                    except Exception as e:
                        logging.error(f"Error parsing analysis for row {idx}: {str(e)}")
                        continue

                # Сохраняем результаты
                results_df.to_excel(formatted_results, index=False)
                
                # Обновляем задачу
                search_task.status = 'completed'
                search_task.result_file = formatted_results
                search_task.completed_at = datetime.utcnow()
                db.session.commit()

                return {'status': 'success'}

        except Exception as e:
            logging.error(f"Task failed: {str(e)}")
            search_task.status = 'failed'
            search_task.error = str(e)
            db.session.commit()
            return {'status': 'failed', 'error': str(e)}

    return asyncio.run(async_search())
