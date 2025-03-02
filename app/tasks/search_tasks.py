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
import openpyxl.styles
from app.models.analysis_result import AnalysisResult
import ast
from typing import List, Any
import openpyxl
from app.tasks.analyze_only import analyze_data, parse_analysis

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
        model_name="gpt-4o-mini",
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
            client_dir = os.path.join('results', str(search_task.client_id))
            os.makedirs(client_dir, exist_ok=True)

            # Пути к файлам
            raw_results = os.path.join(client_dir, 'search_results.csv')
            cleaned_results = os.path.join(client_dir, 'search_results_cleaned.csv')
            analyzed_results = os.path.join(client_dir, 'search_results_analyzed.csv')
            
            # 1. Поиск и сохранение статей
            search_task.stage = 'search'
            db.session.commit()
            send_task_log(task_id, "Starting search...", 'search', 0, 0)
            
            total_queries = len(search_query.main_phrases.split('\n'))
            for idx, query in enumerate(search_query.main_phrases.split('\n'), 1):
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
                            # Добавляем поисковый запрос к каждой строке
                            df['search_query'] = query.strip()
                            # Создаем файл если его нет
                            if os.path.exists(raw_results):
                                df.to_csv(raw_results, mode='a', header=False, index=False)
                            else:
                                df.to_csv(raw_results, index=False)
                            
                    # Обновляем прогресс поиска
                    search_progress = int((idx / total_queries) * 100)
                    send_task_log(task_id, f"Processed query {idx}/{total_queries}", 'search', search_progress // 3, search_progress)
                    
                except Exception as e:
                    send_task_log(task_id, f"Error: {str(e)}", 'search')
                    continue

            if not os.path.exists(raw_results) or os.path.getsize(raw_results) == 0:
                raise ValueError("No search results found for any query")

            # 2. Очистка данных
            search_task.stage = 'clean'
            db.session.commit()
            send_task_log(task_id, "Starting data cleaning...", 'clean', 33, 0)
            
            if os.path.exists(raw_results):
                df = pd.read_csv(raw_results)
                df_cleaned = clean_data(df, task_id)
                df_cleaned.to_csv(cleaned_results, index=False)
                send_task_log(task_id, "Data cleaning completed", 'clean', 66, 100)
            else:
                raise ValueError("No search results found")

            # 3. Анализ данных
            search_task.stage = 'analyze'
            db.session.commit()
            send_task_log(task_id, "Starting analysis...", 'analyze', 66, 0)
            
            if os.path.exists(cleaned_results):
                await run_analyse_data(cleaned_results, analyzed_results, prompt.content, {
                    'model': 'gpt-4o-mini',
                    'api_keys': os.getenv('OPENAI_API_KEYS', '').split(','),
                    'max_retries': 3,
                    'max_rate': 500
                }, task_id)
            else:
                raise ValueError("No cleaned data found")

            # 4. Форматирование результатов
            if os.path.exists(analyzed_results):
                results_df = pd.read_csv(analyzed_results)
                
                # Получаем названия колонок из промпта
                column_names = [name.strip() for name in (prompt.column_names or '').split('\n') if name.strip()]
                
                # Разбираем ответы модели в новые колонки
                for idx, row in results_df.iterrows():
                    try:
                        if pd.isna(row['analysis']):
                            values = [None] * len(column_names)
                        else:
                            values = parse_analysis(row['analysis'], column_names)
                        
                        # Добавляем значения в DataFrame
                        for col, value in zip(column_names, values):
                            results_df.at[idx, col] = value
                            
                    except Exception as e:
                        logging.error(f"Error processing row {idx}: {str(e)}")
                        # В случае ошибки заполняем None
                        for col in column_names:
                            results_df.at[idx, col] = None
                
                # Удаляем только колонку analysis, сохраняя search_query
                results_df = results_df.drop('analysis', axis=1)
                
                # Сохраняем результаты в CSV
                formatted_results = os.path.join(client_dir, f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                results_df.to_csv(formatted_results, index=False, encoding='utf-8-sig')

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

@celery.task(bind=True)
def run_search_and_clean(self, task_id):
    """Асинхронная задача для выполнения поиска и очистки данных"""
    async def async_search():
        search_task = SearchTask.query.get(task_id)
        if not search_task:
            return {'status': 'failed', 'error': 'Task not found'}
        
        try:
            # Получаем параметры поиска из БД
            search_query = SearchQuery.query.get(search_task.search_query_id)
            if not search_query:
                raise ValueError("Search query not found")

            # Создаем директории для результатов
            client_dir = os.path.join('results', str(search_task.client_id))
            os.makedirs(client_dir, exist_ok=True)

            # Пути к файлам
            raw_results = os.path.join(client_dir, 'search_results.csv')
            cleaned_results = os.path.join(client_dir, 'search_results_cleaned.csv')
            
            # 1. Поиск и сохранение статей
            search_task.stage = 'search'
            db.session.commit()
            send_task_log(task_id, "Starting search...", 'search', 0, 0)
            
            total_queries = len(search_query.main_phrases.split('\n'))
            for idx, query in enumerate(search_query.main_phrases.split('\n'), 1):
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
                            # Добавляем поисковый запрос к каждой строке
                            df['search_query'] = query.strip()
                            # Создаем файл если его нет
                            if os.path.exists(raw_results):
                                df.to_csv(raw_results, mode='a', header=False, index=False)
                            else:
                                df.to_csv(raw_results, index=False)
                    
                    # Обновляем прогресс поиска
                    search_progress = int((idx / total_queries) * 100)
                    send_task_log(task_id, f"Processed query {idx}/{total_queries}", 'search', search_progress // 3, search_progress)
                    
                except Exception as e:
                    send_task_log(task_id, f"Error: {str(e)}", 'search')
                    continue

            if not os.path.exists(raw_results) or os.path.getsize(raw_results) == 0:
                raise ValueError("No search results found for any query")

            # 2. Очистка данных
            search_task.stage = 'clean'
            db.session.commit()
            send_task_log(task_id, "Starting data cleaning...", 'clean', 33, 0)
            
            if os.path.exists(raw_results):
                df = pd.read_csv(raw_results)
                df_cleaned = clean_data(df, task_id)
                df_cleaned.to_csv(cleaned_results, index=False)
                send_task_log(task_id, "Data cleaning completed", 'clean', 66, 100)
            else:
                raise ValueError("No search results found")

            # Обновляем задачу
            search_task.status = 'completed'
            search_task.result_file = cleaned_results
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

@celery.task(bind=True)
def run_analysis(self, task_id, cleaned_file=None):
    """Асинхронная задача для выполнения анализа данных"""
    async def async_analyze():
        search_task = SearchTask.query.get(task_id)
        if not search_task:
            return {'status': 'failed', 'error': 'Task not found'}
        
        try:
            # Получаем активный промпт
            prompt = Prompt.query.filter_by(
                client_id=search_task.client_id,
                is_active=True
            ).first()
            if not prompt:
                raise ValueError("No active prompt found")

            # Создаем директории для результатов
            client_dir = os.path.join('results', str(search_task.client_id))
            os.makedirs(client_dir, exist_ok=True)

            # Определяем входной файл
            if cleaned_file and os.path.exists(cleaned_file):
                input_file = cleaned_file
            else:
                input_file = os.path.join(client_dir, 'search_results_cleaned.csv')
                if not os.path.exists(input_file):
                    raise ValueError("No cleaned data file found")

            # Путь для результатов анализа
            analyzed_results = os.path.join(client_dir, 'search_results_analyzed.csv')
            
            # Запускаем анализ с новым модулем
            await analyze_data(input_file, analyzed_results, prompt.content, {
                    'model': 'gpt-4o-mini',
                    'api_keys': os.getenv('OPENAI_API_KEYS', '').split(','),
                    'max_retries': 3,
                    'max_rate': 500
            }, task_id)

            # Форматируем результаты
            if os.path.exists(analyzed_results):
                # Читаем исходные данные и результаты анализа
                input_df = pd.read_csv(input_file)
                results_df = pd.read_csv(analyzed_results)
                
                # Получаем названия колонок из промпта
                column_names = [name.strip() for name in (prompt.column_names or '').split('\n') if name.strip()]
                logging.info(f"Column names from prompt: {column_names}")
                
                # Разбираем ответы модели в новые колонки
                for idx, row in results_df.iterrows():
                    try:
                        # Создаем запись в БД
                        analysis_result = AnalysisResult(
                            task_id=task_id,
                            prompt_id=prompt.id,
                            title=input_df.iloc[idx]['title'],
                            url=input_df.iloc[idx]['link'],
                            content=input_df.iloc[idx]['description']
                        )
                        
                        if pd.isna(row['analysis']):
                            values = [None] * len(column_names)
                            logging.warning(f"Empty analysis for row {idx}")
                        else:
                            logging.info(f"Raw analysis for row {idx}: {row['analysis']}")
                            values = parse_analysis(row['analysis'], column_names)
                            logging.info(f"Parsed values for row {idx}: {values}")
                        
                        # Добавляем значения в DataFrame и в БД
                        for col, value in zip(column_names, values):
                            results_df.at[idx, col] = value
                            # Устанавливаем значение в модель БД если есть соответствующее поле
                            if hasattr(analysis_result, col.lower()):
                                setattr(analysis_result, col.lower(), value)
                                logging.info(f"Set DB field {col.lower()} = {value}")
                            else:
                                logging.warning(f"No DB field for column {col}")
                                
                        db.session.add(analysis_result)
                            
                    except Exception as e:
                        logging.error(f"Error processing row {idx}: {str(e)}")
                        # В случае ошибки заполняем None
                        for col in column_names:
                            results_df.at[idx, col] = None
                
                # Сохраняем все в БД
                db.session.commit()
                logging.info("Saved all results to DB")
                
                # Удаляем только колонку analysis, сохраняя search_query
                results_df = results_df.drop('analysis', axis=1)
                
                # Сохраняем результаты в CSV
                formatted_results = os.path.join(client_dir, f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                results_df.to_csv(formatted_results, index=False, encoding='utf-8-sig')
                logging.info(f"Saved formatted results to {formatted_results}")

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

    return asyncio.run(async_analyze())
