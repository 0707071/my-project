from app import celery, db
from app.models.task import SearchTask
from app.models.search_query import SearchQuery
from app.models.search_result import SearchResult
from app.models.prompt import Prompt
from app.websockets import send_task_log
from datetime import datetime
import os
import sys
import pandas as pd
import asyncio
import json
import shutil

# Добавляем путь к модулям поиска
sys.path.append(os.path.join(os.path.dirname(__file__), '../../modules'))

from fetch_data import fetch_xmlstock_search_results, fetch_and_parse, process_search_results
from clean_data import clean_data
from analyse_data import run_analyse_data

@celery.task(bind=True)
def run_search(self, task_id):
    """
    Асинхронная задача для выполнения поиска и анализа
    """
    async def async_search():
        search_task = SearchTask.query.get(task_id)
        if not search_task:
            return {'status': 'failed', 'error': 'Task not found'}
        
        try:
            # 1. Подготовка к поиску
            search_task.status = 'searching'
            search_task.stage = 'search'
            search_task.progress = 0
            db.session.commit()
            send_task_log(task_id, 'Task started')
            
            search_query = SearchQuery.query.get(search_task.search_query_id)
            send_task_log(task_id, 'Search query loaded')
            
            # Создаем директории для результатов с датой и временем
            search_datetime = datetime.now()
            search_dir_name = search_datetime.strftime('%Y-%m-%d_%H-%M-%S')
            client_dir = os.path.join('results', str(search_task.client_id))
            current_search_dir = os.path.join(client_dir, search_dir_name)
            
            # Создаем все необходимые директории
            os.makedirs(client_dir, exist_ok=True)
            os.makedirs(current_search_dir, exist_ok=True)
            
            send_task_log(task_id, f'Created results directory: {current_search_dir}')
            
            # Определяем пути к файлам результатов
            raw_results_file = os.path.join(current_search_dir, 'search_results.csv')
            cleaned_results_file = os.path.join(current_search_dir, 'search_results_cleaned.csv')
            analyzed_results_file = os.path.join(current_search_dir, 'search_results_analyzed.csv')
            
            # Создаем директорию roles и сохраняем конфигурацию
            roles_dir = os.path.join(client_dir, 'roles')
            os.makedirs(roles_dir, exist_ok=True)
            
            # Сохраняем конфигурацию поиска
            search_config = {
                'queries': [q.strip() for q in search_query.main_phrases.split('\n') if q.strip()],
                'include': [w.strip() for w in search_query.include_words.split('\n') if w.strip()] if search_query.include_words else [],
                'exclude': [w.strip() for w in search_query.exclude_words.split('\n') if w.strip()] if search_query.exclude_words else [],
                'days': search_query.days_back,
                'results_per_page': search_query.results_per_page,
                'num_pages': search_query.num_pages,
                'verbose': True,
                'exclude_pdf': False,
                'search_engines': [{
                    'name': 'xmlsearch',
                    'domain': None,
                    'tbm': None,
                    'hl': 'ru',
                    'device': None,
                    'lr': None
                }]
            }
            
            send_task_log(task_id, f'Search configuration:')
            send_task_log(task_id, f'- Days back: {search_config["days"]}')
            send_task_log(task_id, f'- Results per page: {search_config["results_per_page"]}')
            send_task_log(task_id, f'- Number of pages: {search_config["num_pages"]}')
            send_task_log(task_id, f'- Total queries: {len(search_config["queries"])}')
            
            # Сохраняем конфигурацию в обеих директориях
            with open(os.path.join(roles_dir, 'search_query.json'), 'w') as f:
                json.dump(search_config, f, indent=2)
            with open(os.path.join(current_search_dir, 'search_query.json'), 'w') as f:
                json.dump(search_config, f, indent=2)
            
            send_task_log(task_id, f'Search configuration saved')
            
            # 2. Выполнение поиска
            data_fetched = False
            total_queries = len(search_config['queries'])
            total_results = 0
            total_saved = 0  # Инициализируем счетчик сохраненных статей
            
            for i, query in enumerate(search_config['queries'], 1):
                send_task_log(
                    task_id, 
                    f'Processing query {i}/{total_queries}: {query}',
                    stage='search',
                    progress=int((i / total_queries) * 100)
                )
                
                # Получаем результаты поиска
                search_results = await fetch_xmlstock_search_results(
                    query,
                    ' '.join(search_config['include']),
                    ' '.join(search_config['exclude']),
                    search_config
                )
                
                if search_results:
                    send_task_log(
                        task_id, 
                        f'Found {len(search_results)} results for query: {query}',
                        stage='search'
                    )
                    total_results += len(search_results)
                    
                    # Парсим статьи
                    articles = await process_search_results(search_results)
                    successful_articles = [a for a in articles if a is not None]
                    send_task_log(
                        task_id,
                        f'Successfully parsed {len(successful_articles)} out of {len(articles)} articles',
                        stage='search'
                    )
                    
                    # Сохраняем результаты
                    processed_articles = []
                    for search_result, article in zip(search_results, articles):
                        if article:
                            processed_article = {
                                'title': search_result.get('title', ''),
                                'url': search_result.get('link', ''),
                                'published_date': search_result.get('pubDate', ''),
                                'domain': search_result.get('domain', ''),
                                'description': article.get('text', '')[:5000],
                                'query': query,
                                'snippet': search_result.get('snippet', '')
                            }
                            processed_articles.append(processed_article)
                    
                    # Сохраняем в CSV с правильными заголовками
                    if processed_articles:
                        df = pd.DataFrame(processed_articles)
                        # Определяем заголовки
                        headers = ['title', 'url', 'published_date', 'domain', 'description', 'query', 'snippet']
                        
                        # Если файл не существует, создаем с заголовками
                        if not os.path.exists(raw_results_file):
                            df.to_csv(raw_results_file, index=False, columns=headers)
                            send_task_log(task_id, f'Created new results file with {len(processed_articles)} articles')
                        else:
                            # Добавляем данные без заголовков
                            df.to_csv(raw_results_file, mode='a', header=False, index=False, columns=headers)
                            send_task_log(task_id, f'Appended {len(processed_articles)} articles to existing file')
                        
                        data_fetched = True
                        total_saved += len(processed_articles)
                        send_task_log(task_id, f'Total articles saved so far: {total_saved}')
                else:
                    send_task_log(task_id, f'No results found for query: {query}')
            
            send_task_log(task_id, f'Total results found: {total_results}')
            
            if not data_fetched:
                raise ValueError("No search results found for any query")
            
            search_task.progress = 33
            db.session.commit()
            
            # 3. Очистка данных
            search_task.status = 'cleaning'
            search_task.stage = 'clean'
            db.session.commit()
            send_task_log(task_id, 'Starting data cleaning...', stage='clean', progress=0)
            
            if os.path.exists(raw_results_file) and os.path.getsize(raw_results_file) > 0:
                rows_before, rows_after = clean_data(raw_results_file, cleaned_results_file, verbose=True)
                send_task_log(
                    task_id, 
                    f'Cleaned data: {rows_before} rows before, {rows_after} rows after',
                    stage='clean',
                    progress=100
                )
            else:
                raise ValueError("No data found in raw results file")
            
            search_task.progress = 66
            db.session.commit()
            
            # 4. Анализ с помощью LLM
            search_task.status = 'analyzing'
            search_task.stage = 'analyze'
            db.session.commit()
            send_task_log(task_id, 'Starting LLM analysis...', stage='analyze', progress=0)
            
            # Получаем активный промпт для клиента
            prompt = Prompt.query.filter_by(
                client_id=search_task.client_id,
                is_active=True
            ).first()
            
            if not prompt:
                raise ValueError("No active prompt found for this client")
            
            # Сохраняем промпт
            with open(os.path.join(roles_dir, 'prompt.txt'), 'w') as f:
                f.write(prompt.content)
                send_task_log(task_id, f'Saved prompt: {prompt.content[:200]}...')
            
            # Анализируем статьи
            await run_analyse_data(cleaned_results_file, analyzed_results_file, roles_dir, search_config)
            send_task_log(task_id, 'Analysis completed', stage='analyze', progress=100)
            
            # Проверяем результаты анализа
            results_df = pd.read_csv(analyzed_results_file)
            total_articles = len(results_df)
            articles_with_analysis = results_df['analysis'].notna().sum()
            
            send_task_log(
                task_id, 
                f'Analysis completed. Analyzed {articles_with_analysis} out of {total_articles} articles',
                stage='analyze',
                progress=100
            )
            
            # Сохраняем результаты в БД и в файл
            if os.path.exists(analyzed_results_file):
                results_df = pd.read_csv(analyzed_results_file)
                for _, row in results_df.iterrows():
                    # Парсим анализ из строки в список
                    try:
                        analysis_list = eval(row['analysis'])
                        result = SearchResult(
                            task_id=task_id,
                            url=row['url'],
                            title=row['title'],
                            content=row['description'],
                            analysis=row['analysis'],
                            published_date=row.get('published_date'),
                            domain=row.get('domain'),
                            snippet=row.get('snippet', ''),
                            # Разбираем ответ LLM
                            company_name=analysis_list[0],
                            potential_score=analysis_list[1] if isinstance(analysis_list[1], int) else None,
                            sales_notes=analysis_list[2],
                            company_description=analysis_list[3],
                            annual_revenue=float(analysis_list[4]) if analysis_list[4] != 'NA' else None,
                            country=analysis_list[5],
                            website=analysis_list[6] if analysis_list[6] != 'NA' else None,
                            assumed_website=analysis_list[7] if analysis_list[7] != 'NA' else None
                        )
                    except Exception as e:
                        print(f"Error parsing analysis: {str(e)}")
                        result = SearchResult(
                            task_id=task_id,
                            url=row['url'],
                            title=row['title'],
                            content=row['description'],
                            analysis=row['analysis'],
                            published_date=row.get('published_date'),
                            domain=row.get('domain'),
                            snippet=row.get('snippet', '')
                        )
                    db.session.add(result)
                
                db.session.commit()
                send_task_log(task_id, f'Saved {len(results_df)} results to database')
            else:
                raise ValueError("No analyzed results file found")
            
            # Завершаем задачу
            search_task.status = 'completed'
            search_task.progress = 100
            search_task.completed_at = datetime.utcnow()
            search_task.result_file = analyzed_results_file
            db.session.commit()
            send_task_log(task_id, 'Task completed successfully')
            
            return {'status': 'success', 'task_id': task_id}
            
        except Exception as e:
            error_message = f'Error: {str(e)}'
            search_task.status = 'failed'
            search_task.error_message = error_message
            db.session.commit()
            send_task_log(task_id, error_message)
            return {'status': 'failed', 'error': error_message}

    # Запускаем асинхронную функцию
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_search())
