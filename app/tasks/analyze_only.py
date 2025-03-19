import pandas as pd
import logging
import json
import ast
from typing import List, Dict, Any
from modules.llm_clients import get_llm_client
from app.websockets import send_task_log
import os

def parse_analysis(analysis_str: str, column_names: List[str]) -> List[str]:
    """
    Парсит ответ модели с обработкой ошибок.
    При ошибке парсинга возвращает сырой ответ в первой колонке и "Err" в остальных.
    """
    if not analysis_str or pd.isna(analysis_str):
        return [None] * len(column_names)
        
    try:
        # Пробуем разные методы парсинга
        try:
            # Сначала как JSON
            data = json.loads(analysis_str)
            values = list(data.values()) if isinstance(data, dict) else data
        except json.JSONDecodeError:
            try:
                # Затем как Python literal
                values = ast.literal_eval(analysis_str)
            except (SyntaxError, ValueError):
                # Если не получилось распарсить - возвращаем сырой ответ
                return [analysis_str] + ["Err"] * (len(column_names) - 1)
        
        # Приводим все значения к строкам
        values = [
            str(v).strip() if v is not None else None 
            for v in values
        ]
        
        # Дополняем или обрезаем до нужной длины
        if len(values) < len(column_names):
            values.extend([None] * (len(column_names) - len(values)))
        else:
            values = values[:len(column_names)]
            
        return values
        
    except Exception as e:
        logging.error(f"Error parsing analysis: {str(e)}\nRaw response: {analysis_str}")
        return [str(analysis_str)] + ["Err"] * (len(column_names) - 1)

async def analyze_data(input_filename: str, output_filename: str, prompt_content: str, config: Dict[str, Any], task_id: int = None) -> None:
    """
    Анализирует данные с помощью LLM.
    При ошибках в ответе модели сохраняет сырой ответ.
    """
    try:
        # Загружаем данные
        df = pd.read_csv(input_filename)
        if df.empty:
            logging.warning("No data to analyze")
            return
        
        # Создаем директорию для output_filename если её нет
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        # Получаем LLM клиент
        llm_client = get_llm_client(
            model_name=config.get('model', 'gpt-4o-mini'),
            config=config
        )
        
        total_articles = len(df)
        if task_id:
            send_task_log(task_id, f"Starting analysis of {total_articles} articles", 'analyze', 66, 0)
            
        # Анализируем каждую статью
        for index, row in df.iterrows():
            try:
                if pd.isna(row['description']) or len(str(row['description'])) < 100:
                    df.at[index, 'analysis'] = "Error: Invalid content"
                    continue

                article_text = f"Title: {row['title']}\n\nContent: {row['description']}"
                messages = [
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": article_text}
                ]
                
                try:
                    # Получаем ответ от модели
                    response = await llm_client.get_completion(messages)
                    
                    # Сохраняем ответ как есть, даже если это не JSON
                    # Парсинг будет выполнен позже
                    df.at[index, 'analysis'] = response
                    
                    # Обновляем прогресс
                    if task_id:
                        progress = int((index + 1) / total_articles * 100)
                        send_task_log(
                            task_id, 
                            f"Analyzed article {index + 1}/{total_articles}", 
                            'analyze', 
                            66 + progress // 3,  # Общий прогресс
                            progress  # Прогресс этапа
                        )
                    
                except Exception as e:
                    error_msg = f"Error getting model response: {str(e)}"
                    df.at[index, 'analysis'] = error_msg
                    logging.error(f"Article {index + 1}: {error_msg}")
                    if task_id:
                        send_task_log(task_id, error_msg, 'analyze')
                
                # Сохраняем каждые 3 статьи в тот же файл
                if (index + 1) % 3 == 0:
                    df.to_csv(output_filename, index=False, encoding='utf-8-sig')
            
            except Exception as e:
                error_msg = f"Error analyzing article: {str(e)}"
                df.at[index, 'analysis'] = error_msg
                logging.error(f"Article {index}: {error_msg}")
                if task_id:
                    send_task_log(task_id, error_msg, 'analyze')
                df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        
        # Финальное сохранение
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        if task_id:
            send_task_log(task_id, "Analysis completed", 'analyze', 100, 100)
        
    except Exception as e:
        error_msg = f"Critical error in analysis: {str(e)}"
        logging.error(error_msg)
        if task_id:
            send_task_log(task_id, error_msg, 'analyze')
        raise 