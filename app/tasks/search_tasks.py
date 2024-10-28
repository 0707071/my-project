from app import celery, db
from app.models.task import SearchTask
from app.models.search_query import SearchQuery
from app.models.search_result import SearchResult
from app.websockets import send_task_log
from datetime import datetime
import time
import os
import sys

# Добавляем путь к модулям поиска в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../../modules'))

from fetch_data import fetch_xmlstock_search_results, fetch_and_save_articles

@celery.task(bind=True)
def run_search(self, task_id):
    """
    Асинхронная задача для выполнения поиска
    """
    search_task = SearchTask.query.get(task_id)
    if not search_task:
        return {'status': 'failed', 'error': 'Task not found'}
    
    try:
        # Обновляем статус
        search_task.status = 'running'
        search_task.progress = 0
        db.session.commit()
        send_task_log(task_id, 'Задача запущена')
        
        # Получаем поисковый запрос
        search_query = SearchQuery.query.get(search_task.search_query_id)
        send_task_log(task_id, 'Загружен поисковый запрос')
        
        # Подготавливаем параметры поиска
        search_params = {
            'main_phrases': search_query.main_phrases.split('\n'),
            'include_words': search_query.include_words.split('\n') if search_query.include_words else [],
            'exclude_words': search_query.exclude_words.split('\n') if search_query.exclude_words else []
        }
        
        # Выполняем поиск
        search_task.progress = 10
        db.session.commit()
        send_task_log(task_id, 'Начинаем поиск результатов...')
        
        search_results = fetch_xmlstock_search_results(
            search_params['main_phrases'],
            search_params['include_words'],
            search_params['exclude_words']
        )
        
        search_task.progress = 50
        db.session.commit()
        send_task_log(task_id, f'Найдено {len(search_results)} результатов')
        
        # Получаем контент статей
        total_results = len(search_results)
        send_task_log(task_id, 'Начинаем загрузку контента статей...')
        
        for i, result in enumerate(search_results, 1):
            send_task_log(task_id, f'Обработка статьи {i} из {total_results}: {result["url"]}')
            article_data = fetch_and_save_articles([result['url']])[0]
            
            search_result = SearchResult(
                task_id=task_id,
                url=result['url'],
                title=result['title'],
                snippet=result['snippet'],
                content=article_data.get('content'),
                published_date=article_data.get('published_date'),
                domain=article_data.get('domain')
            )
            db.session.add(search_result)
            
            progress = 50 + int((i / total_results) * 50)
            search_task.progress = progress
            db.session.commit()
            
            self.update_state(state='PROGRESS', meta={'progress': progress})
        
        # Завершаем задачу
        search_task.status = 'completed'
        search_task.completed_at = datetime.utcnow()
        db.session.commit()
        send_task_log(task_id, 'Задача успешно завершена')
        
        return {'status': 'success', 'task_id': task_id}
        
    except Exception as e:
        error_message = f'Ошибка: {str(e)}'
        search_task.status = 'failed'
        search_task.error_message = error_message
        db.session.commit()
        send_task_log(task_id, error_message)
        return {'status': 'failed', 'error': error_message}
