import os
import sys
import re
import json
import time
import asyncio
import aiohttp
from itertools import cycle
from functools import wraps
import google.generativeai as genai

# Загрузка конфигурации
try:
    with open('config/search_config.json', 'r') as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print("Ошибка при чтении файла конфигурации. Используем значения по умолчанию.")
    config = {}

# Загрузка API ключей
try:
    from config.api_keys import api_keys
except ImportError:
    print("Ошибка при импорте api_keys. Убедитесь, что файл существует и содержит необходимые ключи.")
    api_keys = {}

use_gemini = config.get("use_gemini", True)
gemini_rate_limit = config.get("gemini_rate_limit", 20)  # Запросов в минуту
gemini_api_keys = api_keys.get("gemini_api_keys", [])

if not gemini_api_keys:
    print("Внимание: Список ключей API Gemini пуст. Убедитесь, что ключи правильно настроены в файле api_keys.py")

gemini_key_cycle = cycle(gemini_api_keys)

def clean_domain(domain):
    """
    Очищает доменное имя от префиксов.
    
    Args:
        domain (str): Исходный домен.
    
    Returns:
        str: Очищенный домен.
    """
    domain = domain.lower()
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    return domain.split('/')[0]

async def rate_limited_request(session, url, payload, api_key):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    async with session.post(url, json=payload, headers=headers) as response:
        return await response.json()

async def gpt_query_async(messages, timeout=120, max_retries=3):
    if use_gemini:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={next(gemini_key_cycle)}"
        payload = {
            "contents": [{"parts": [{"text": msg['content']} for msg in messages]}]
        }

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    response = await asyncio.wait_for(
                        session.post(url, json=payload),
                        timeout=timeout
                    )
                    response_json = await response.json()
                    
                    if 'error' in response_json:
                        error_message = response_json['error'].get('message', 'Неизвестная ошибка')
                        print(f"Ошибка API Gemini (попытка {attempt + 1}): {error_message}")
                        
                        if "Resource has been exhausted" in error_message:
                            if attempt < max_retries - 1:
                                print(f"Ожидание 60 секунд перед следующей попыткой...")
                                await asyncio.sleep(60)
                                continue
                        
                        if attempt == max_retries - 1:
                            return f"Ошибка API: {error_message}", 0
                        continue
                    
                    if 'candidates' not in response_json:
                        print(f"Неожиданный формат ответа API Gemini: {response_json}")
                        if attempt == max_retries - 1:
                            return "Неожиданный формат ответа API", 0
                        continue
                    
                    content = response_json['candidates'][0]['content']['parts'][0]['text']
                    tokens_used = len(' '.join(msg['content'] for msg in messages).split()) + len(content.split())
                    return content, tokens_used
                
            except asyncio.TimeoutError:
                print(f"Timeout: Запрос не выполнен за {timeout} секунд.")
                if attempt == max_retries - 1:
                    return "timeout", 0
            except Exception as e:
                print(f"Ошибка в запросе к API Gemini: {e}")
                if attempt == max_retries - 1:
                    return str(e), 0
            
            # Ожидание перед следующей попыткой
            if attempt < max_retries - 1:
                await asyncio.sleep(5)
    else:
        # Здесь может быть реализована асинхронная версия для OpenAI GPT-4
        print("Асинхронная версия для OpenAI GPT-4 не реализована")
        return "Not implemented", 0


# async def process_queries(queries):
#     delay = 60 / gemini_rate_limit  # Задержка между запросами
#     tasks = []
#     for query in queries:
#         task = asyncio.create_task(gpt_query_async(query))
#         tasks.append(task)
#         await asyncio.sleep(delay)
#     return await asyncio.gather(*tasks)

def load_role_description(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

def signal_handler(sig, frame, workbook, filename, verbose=False):
    if verbose:
        print('Вы нажали Control+C! Сохранение и закрытие файла...')
    workbook.save(filename)
    workbook.close()
    sys.exit(0)

def save_results_to_csv(results, output_filename, verbose=False):
    df = pd.DataFrame(results)
    df.to_csv(output_filename, index=False)
    if verbose:
        print(f"Результаты успешно сохранены в файл: {output_filename}")

def clean_text(text):
    """Очищает текст от нежелательных символов."""
    return re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', str(text))

def format_value(value):
    """Форматирует значение, делая первую букву заглавной."""
    if isinstance(value, str) and value:
        return value[0].upper() + value[1:].lower()
    return value

def truncate_text(text, max_length=10000):
    """Обрезает текст до заданной максимальной длины."""
    return text[:max_length] if len(text) > max_length else text

def clean_linkedin_link(link):
    """Очищает ссылку LinkedIn от дополнительных параметров."""
    if "linkedin.com" in link:
        return link.split('?')[0]
    return link

def load_config(config_file):
    """
    Загружает конфигурацию из JSON файла.
    
    Args:
        config_file (str): Путь к файлу конфигурации.
    
    Returns:
        dict: Загруженная конфигурация.
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Файл конфигурации не найден: {config_file}")
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка при чтении файла конфигурации: {config_file}")
        return {}