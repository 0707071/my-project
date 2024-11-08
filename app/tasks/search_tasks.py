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

            # 1. Поиск (33%)
            total_queries = len(search_query.main_phrases.split('\n'))
            send_task_log(task_id, "Starting search phase...", 'search', 0)
            
            for i, query in enumerate(search_query.main_phrases.split('\n'), 1):
                if not query.strip():
                    continue
                
                try:
                    send_task_log(task_id, f"Processing query: {query}", 'search')
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
                        send_task_log(task_id, f"Found {len(search_results)} results", 'search')
                        articles = await process_search_results(search_results)
                        if articles:
                            send_task_log(task_id, f"Successfully parsed {len(articles)} articles", 'search')
                            df = pd.DataFrame(articles)
                            if os.path.exists(raw_results):
                                df.to_csv(raw_results, mode='a', header=False, index=False)
                            else:
                                df.to_csv(raw_results, index=False)
                    search_progress = int((i / total_queries) * 33)
                    send_task_log(task_id, None, 'search', search_progress)
                except Exception as e:
                    send_task_log(task_id, f"Error: {str(e)}", 'search')
                    continue

            if not os.path.exists(raw_results) or os.path.getsize(raw_results) == 0:
                raise ValueError("No search results found for any query")

            # 2. Очистка (33-66%)
            send_task_log(task_id, "Starting data cleaning...", 'clean', 33)
            df = pd.read_csv(raw_results)
            total_rows = len(df)
            df_cleaned = clean_data(df)
            cleaned_rows = len(df_cleaned)
            send_task_log(task_id, f"Removed {total_rows - cleaned_rows} duplicates", 'clean')
            df_cleaned.to_csv(cleaned_results, index=False)
            send_task_log(task_id, "Data cleaning completed", 'clean', 66)

            # 3. Анализ (66-100%)
            send_task_log(task_id, "Starting analysis...", 'analyze', 66)
            total_articles = len(df_cleaned)
            for i, row in enumerate(df_cleaned.iterrows(), 1):
                try:
                    # ... код анализа ...
                    analyze_progress = 66 + int((i / total_articles) * 34)
                    send_task_log(task_id, f"Analyzed article: {row['title'][:50]}...", 'analyze', analyze_progress)
                except Exception as e:
                    send_task_log(task_id, f"Error analyzing article: {str(e)}", 'analyze')
                    continue

            send_task_log(task_id, "Analysis completed", 'analyze', 100)

            # 4. Форматирование результатов
            if os.path.exists(analyzed_results):
                results_df = pd.read_csv(analyzed_results)
                
                # Получаем названия колонок из промпта в БД
                column_names = [name.strip() for name in (prompt.column_names or '').split('\n') if name.strip()]
                
                # Разбираем ответы модели и сохраняем в БД
                for idx, row in results_df.iterrows():
                    try:
                        analysis = eval(row['analysis'])
                        if isinstance(analysis, list) and len(analysis) >= len(column_names):
                            # Создаем запись в БД
                            result = AnalysisResult(
                                task_id=task_id,
                                prompt_id=prompt.id,
                                title=row.get('title'),
                                url=row.get('link'),
                                content=row.get('description'),
                                company_name=analysis[0],
                                potential=analysis[1],
                                sales_notes=analysis[2],
                                company_description=analysis[3],
                                revenue=analysis[4],
                                country=analysis[5],
                                website=analysis[6],
                                article_date=parse_relative_date(row.get('pubDate'))
                            )
                            db.session.add(result)
                    except Exception as e:
                        logging.error(f"Error saving result to DB: {str(e)}")
                
                db.session.commit()

                # Создаем новый датафрейм только с нужными колонками
                results_df = pd.DataFrame(formatted_data)
                
                # Сохраняем с форматированием
                with pd.ExcelWriter(formatted_results, engine='openpyxl') as writer:
                    results_df.to_excel(writer, index=False)
                    
                    # Получаем рабочий лист
                    worksheet = writer.sheets['Sheet1']
                    
                    # Устанавливаем высоту строк и ширину колонок
                    worksheet.row_dimensions[1].height = 30  # Заголовок
                    for i in range(2, len(results_df) + 2):
                        worksheet.row_dimensions[i].height = 75
                        
                    for column in worksheet.columns:
                        max_length = 0
                        column = list(column)
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = min(len(str(cell.value)), 150)
                            except:
                                pass
                        adjusted_width = (max_length + 2)
                        worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
                        
                        # Форматирование ячеек
                        for cell in column:
                            cell.alignment = openpyxl.styles.Alignment(
                                wrap_text=True,
                                vertical='top'
                            )
                
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
