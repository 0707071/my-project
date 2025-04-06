# Path: modules/fetch_data.py
# This file retrieves data from search engines and downloads articles from webpages.

import os
import asyncio
import aiohttp
import pandas as pd
import time
import xml.etree.ElementTree as ET
from newspaper import Article, ArticleException
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any
import logging
from urllib.parse import urlparse
import hashlib

# Загружаем переменные окружения из .env файла
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(basedir, '.env')

print(f"DEBUG: Looking for .env at: {env_path}")
print(f"DEBUG: File exists: {os.path.exists(env_path)}")

# Принудительно перезагружаем .env
load_dotenv(env_path, override=True)

# Получаем данные для авторизации из переменных окружения
XMLSTOCK_USER = os.getenv("XMLSTOCK_USER")
XMLSTOCK_KEY = os.getenv("XMLSTOCK_KEY")
XMLSTOCK_URL = "https://xmlstock.com/google/xml/"

print(f"DEBUG: Environment variables:")
print(f"XMLSTOCK_USER: {XMLSTOCK_USER}")
print(f"XMLSTOCK_KEY: {XMLSTOCK_KEY}")
print(f"Key length: {len(XMLSTOCK_KEY) if XMLSTOCK_KEY else 'None'}")

# Добавим отладочный вывод
print(f"DEBUG: Loading XML Stock credentials from {basedir}/.env")
print(f"User: {XMLSTOCK_USER}")
print(f"Key: {XMLSTOCK_KEY}")

# Семафор для ограничения количества одновременных запросов
MAX_CONCURRENT_REQUESTS = 100
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# Задержка между запросами в секундах
REQUEST_DELAY = 0.1

async def fetch_xmlstock_search_results(query, include, exclude, config, verbose=False):
    """
    Асинхронно получает результаты поиска из API xmlstock.
    Применяет подход умножения для комбинаций ключевых слов и включаемых слов.
    """
    if not XMLSTOCK_USER or not XMLSTOCK_KEY:
        raise ValueError("XMLSTOCK API credentials not found in environment variables")

    # Разбиваем запрос и включаемые слова на отдельные строки
    keyword_phrases = [kw.strip() for kw in query.split('\n') if kw.strip()]
    include_phrases = [inc.strip() for inc in include.split('\n') if inc.strip()] if include else []

    # Если нет включаемых слов, просто используем ключевые фразы
    if not include_phrases:
        include_phrases = [""]

    # Формируем строку исключаемых слов
    exclude_str = f" {exclude}" if exclude else ""

    # Создаем все комбинации ключевых фраз и включаемых слов
    all_queries = []
    for keyword in keyword_phrases:
        for include_word in include_phrases:
            if include_word:
                full_query = f"{keyword} \"{include_word}\"{exclude_str}"
            else:
                full_query = f"{keyword}{exclude_str}"
            all_queries.append(full_query)

    if verbose:
        print(f"Generated {len(all_queries)} queries using multiplication approach:")
        for idx, q in enumerate(all_queries, 1):
            print(f"{idx}. {q}")

    # Обрабатываем все сгенерированные запросы
    if not all_queries:
        print("No valid queries generated")
        return []

    print("Using XMLSTOCK API")

    # Обрабатываем каждый запрос
    all_results = []

    async with aiohttp.ClientSession()  as session:
        # Для каждого запроса из списка комбинаций
        for query_idx, full_query in enumerate(all_queries):
            print(f"\nProcessing query {query_idx + 1}/{len(all_queries)}: {full_query}")
            
            # Правильно формируем параметры запроса
            params = {
                "user": XMLSTOCK_USER,
                "key": XMLSTOCK_KEY,
                "query": full_query,
                "num": config['results_per_page'],  # Количество результатов на страницу
                "tbs": f"qdr:d{config['days']}",  # Количество дней для поиска
                "sort": "date"
            }
            
            print(f"Search parameters: {params}")
            
            query_results = []
            total_results = 0
            
            # Для каждой страницы результатов
            for page in range(config['num_pages']):
                params['start'] = page * config['results_per_page']  # Пагинация
                print(f"Processing page {page + 1}/{config['num_pages']} for query {query_idx + 1}")
                
                async with semaphore:
                    try:
                        async with session.get(XMLSTOCK_URL, params=params, timeout=30) as response:
                            print(f"Response status code: {response.status}")
                            print(f"Request URL: {response.url}")
                            
                            if response.status != 200:
                                print(f"Error fetching results: {response.status}")
                                content = await response.text()
                                print(f"Error response content: {content}")
                                continue

                            content = await response.text()
                            print(f"Raw XML response (first 500 chars): {content[:500]}")
                            
                            root = ET.fromstring(content)
                            page_results = []
                            for group in root.findall('.//group'):
                                for doc in group.findall('doc'):
                                    # Если достигли лимита результатов на странице, прерываем
                                    if len(page_results) >= config['results_per_page']:
                                        break
                                    
                                    pub_date = doc.find('pubDate').text if doc.find('pubDate') is not None else "N/A"
                                    title = doc.find('title').text if doc.find('title') is not None else "N/A"
                                    url = doc.find('url').text if doc.find('url') is not None else "N/A"
                                    snippet = doc.find('snippet').text if doc.find('snippet') is not None else "N/A"
                                    
                                    result = {
                                        'title': title,
                                        'link': url,
                                        'pubDate': pub_date,
                                        'domain': doc.find('displayLink').text if doc.find('displayLink') is not None else "N/A",
                                        'snippet': snippet,
                                        'search_query': full_query  # Добавляем информацию о запросе
                                    }
                                    page_results.append(result)
                                
                                # Если достигли лимита результатов на странице, прерываем
                                if len(page_results) >= config['results_per_page']:
                                    break
                            
                            # Добавляем только нужное количество результатов
                            query_results.extend(page_results[:config['results_per_page']])
                            total_results += len(page_results[:config['results_per_page']])
                            print(f"Results on page {page + 1}: {len(page_results[:config['results_per_page']])}")
                            print(f"Total results for query {query_idx + 1} so far: {total_results}")
                            
                            # Если достигли общего лимита результатов для этого запроса, переходим к следующему
                            if total_results >= config['results_per_page'] * config['num_pages']:
                                break
                        
                    except Exception as e:
                        print(f"Error fetching results for query {query_idx + 1}, page {page}: {str(e)}")
                        print(f"Full error: {repr(e)}")
                    
                    await asyncio.sleep(REQUEST_DELAY)
            
            # Добавляем результаты этого запроса к общим результатам
            all_results.extend(query_results)
            print(f"Added {len(query_results)} results from query {query_idx + 1}")
            print(f"Total results across all queries so far: {len(all_results)}")
        
        # Возвращаем все собранные результаты
        return all_results


async def fetch_and_parse(url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Fetches and parses an article with retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession()  as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 403:
                        logging.warning(f"Access denied (403) for {url}")
                        return None
                    
                    if response.status != 200:
                        logging.warning(f"Failed to fetch {url}, status: {response.status}")
                        if attempt == max_retries - 1:
                            return None
                        continue

                    html = await response.text()
                    
                    # Используем простой подход с newspaper3k
                    article = Article(url)
                    article.set_html(html)
                    article.parse()
                    
                    if article.text and len(article.text.strip()) > 100:
                        return {
                            'text': article.text.strip(),
                            'html': html,
                            'title': article.title
                        }
                    else:
                        logging.warning(f"No valid text found in {url}")

        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(1 * (attempt + 1))

    return None


async def process_search_results(search_results: List[Dict]) -> List[Optional[Dict]]:
    """Process search results with improved error handling"""
    if not search_results:
        logging.warning("No search results to process")
        return []

    tasks = []
    results = []
    
    # Создаем пул задач
    for result in search_results:
        if 'link' in result and result['link']:
            task = asyncio.create_task(fetch_and_parse(result['link']))
            tasks.append((result, task))
    
    if not tasks:
        logging.warning("No valid URLs to process")
        return []

    # Обрабатываем результаты по мере их готовности
    for search_result, task in tasks:
        try:
            article = await task
            if article and article.get('text'):
                processed_article = {
                    'title': search_result.get('title', ''),
                    'link': search_result.get('link', ''),
                    'pubDate': search_result.get('pubDate', ''),
                    'description': article.get('text', '')[:5000],  # Ограничиваем длину текста
                    'domain': urlparse(search_result.get('link', '')).netloc,
                    'snippet': search_result.get('snippet', '')
                }
                results.append(processed_article)
            else:
                logging.warning(f"No valid content for {search_result.get('link')}")
        except Exception as e:
            logging.error(f"Error processing {search_result.get('link')}: {str(e)}")
            continue
    
    return results


async def fetch_and_save_articles(query, include, exclude, config, output_filename, verbose=False, proxy=None):
    """
    Asynchronously fetches search results, processes them, and saves the list of articles.
    
    Args:
        query (str): The search query.
        include (str): Additional terms to include in the search.
        exclude (str): Terms to exclude from the search.
        config (dict): Configuration settings for the search.
        output_filename (str): The filename to save the results.
        verbose (bool, optional): If True, prints detailed output. Default is False.
        proxy (str, optional): Proxy URL if needed. Default is None.
    
    Returns:
        list: List of processed articles.
    """
    search_results = await fetch_xmlstock_search_results(query, include, exclude, config, verbose)
    if not search_results:
        print("No search results found.")
        return []

    articles = await process_search_results(search_results)
    
    processed_articles = []
    for search_result, article in zip(search_results, articles):
        if article:
            processed_article = {
                'title': search_result.get('title', ''),
                'link': search_result.get('link', ''),
                'pubDate': search_result.get('pubDate', ''),
                'description': article.get('description', '')[:5000],  # Ограничиваем длину текста
                'domain': search_result.get('domain', ''),
                'snippet': search_result.get('snippet', '')
            }
            processed_articles.append(processed_article)
    
    # Сохраняем результаты в файл
    if processed_articles:
        df = pd.DataFrame(processed_articles)
        df.to_csv(output_filename, index=False)
        print(f"Saved {len(processed_articles)} articles to {output_filename}")
    else:
        print("No articles to save.")
    
    return processed_articles

