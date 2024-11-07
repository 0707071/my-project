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
MAX_CONCURRENT_REQUESTS = 10
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# Задержка между запросами в секундах
REQUEST_DELAY = 1


async def fetch_xmlstock_search_results(query, include, exclude, config, verbose=False):
    """
    Асинхронно получает результаты поиска из API xmlstock.
    """
    if not XMLSTOCK_USER or not XMLSTOCK_KEY:
        raise ValueError("XMLSTOCK API credentials not found in environment variables")

    results = []
    
    full_query = query
    if include:
        full_query += f" {include}"
    if exclude:
        full_query += f" {exclude}"
    
    print(f"Full search query: {full_query}")
    print("Using XMLSTOCK API")
    
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
    
    async with aiohttp.ClientSession() as session:
        total_results = 0
        for page in range(config['num_pages']):
            params['start'] = page * config['results_per_page']  # Пагинация
            print(f"\nProcessing page {page + 1}/{config['num_pages']}")
            
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
                                    'snippet': snippet
                                }
                                page_results.append(result)
                            
                            # Если достигли лимита результатов на странице, прерываем
                            if len(page_results) >= config['results_per_page']:
                                break
                        
                        # Добавляем только нужное количество результатов
                        results.extend(page_results[:config['results_per_page']])
                        total_results += len(page_results[:config['results_per_page']])
                        print(f"Results on page {page + 1}: {len(page_results[:config['results_per_page']])}")
                        print(f"Total results so far: {total_results}")
                        
                        # Если достигли общего лимита результатов, останавливаемся
                        if total_results >= config['results_per_page'] * config['num_pages']:
                            break
                    
                except Exception as e:
                    print(f"Error fetching results for page {page}: {str(e)}")
                    print(f"Full error: {repr(e)}")
                
                await asyncio.sleep(REQUEST_DELAY)

    # Возвращаем точное количество запрошенных результатов
    max_results = config['results_per_page'] * config['num_pages']
    return results[:max_results]


async def fetch_and_parse(url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Fetches and parses an article with retries and better error handling"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 403:
                        logging.warning(f"Access denied (403) for {url}")
                        # Пробуем через другой User-Agent
                        headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        continue
                    
                    if response.status != 200:
                        logging.warning(f"Failed to fetch {url}, status: {response.status}")
                        if attempt == max_retries - 1:
                            return None
                        continue

                    html = await response.text()
                    
                    # Пробуем разные методы извлечения текста
                    text = None
                    
                    # 1. Newspaper3k
                    try:
                        article = Article('')
                        article.download_state = 2
                        article.html = html
                        article.parse()
                        text = article.text
                    except Exception as e:
                        logging.warning(f"Newspaper3k failed: {str(e)}")
                    
                    # 2. BeautifulSoup если newspaper не сработал
                    if not text or len(text.strip()) < 100:
                        try:
                            soup = BeautifulSoup(html, 'html.parser')
                            for tag in soup(['script', 'style', 'meta', 'noscript', 'header', 'footer', 'nav']):
                                tag.decompose()
                            
                            # Ищем основной контент
                            main_content = soup.find(['article', 'main', 'div'], class_=lambda x: x and any(word in str(x).lower() for word in ['content', 'article', 'main', 'body']))
                            if main_content:
                                text = ' '.join(main_content.stripped_strings)
                            else:
                                text = ' '.join(soup.stripped_strings)
                        except Exception as e:
                            logging.warning(f"BeautifulSoup failed: {str(e)}")
                    
                    if text and len(text.strip()) > 100:
                        return {
                            'text': text.strip(),
                            'html': html,
                            'title': article.title if 'article' in locals() else None
                        }
                    else:
                        logging.warning(f"No valid text found in {url}")

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.warning(f"Attempt {attempt + 1} failed: {str(e)}, url='{url}'")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(1 * (attempt + 1))
        except Exception as e:
            logging.error(f"Unexpected error fetching {url}: {str(e)}")
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

    articles = await process_search_results(search_results, verbose, proxy)
    
    processed_articles = []
    for search_result, article in zip(search_results, articles):
        processed_article = {
            'title': search_result.get('title', ''),
            'link': search_result.get('link', ''),
            'pubDate': search_result.get('pubDate', ''),
            'description': article.get('text', '')[:500],  # Taking first 500 characters as description
            'query': query,
            'analysis': ''  # Placeholder for future analysis
        }
        processed_articles.append(processed_article)

    # Save results after processing the entire search query
    df = pd.DataFrame(processed_articles)
    if os.path.exists(output_filename):
        df.to_csv(output_filename, mode='a', header=False, index=False)
    else:
        df.to_csv(output_filename, index=False)

    print(f"Saved {len(processed_articles)} articles for query: {query}")
    return processed_articles


def save_results_to_csv(results, output_filename, verbose=False):
    """
    Saves the results to a CSV file.
    
    Args:
        results (list): List of results to save.
        output_filename (str): The filename to save the results.
        verbose (bool, optional): If True, prints detailed output. Default is False.
    """
    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_filename, index=False)
        if verbose:
            print(f"Extracted articles saved to '{output_filename}'")
    else:
        if verbose:
            print("No articles were extracted.")


def extract_text(html: str) -> str:
    """Извлекает текст из HTML используя newspaper3k и BeautifulSoup как запасной вариант"""
    try:
        # Пробуем newspaper3k
        article = Article('')
        article.download_state = 2  # Пропускаем скачивание
        article.html = html
        article.parse()
        text = article.text
        
        if text and len(text.strip()) > 100:
            return text.strip()
    except (ArticleException, Exception) as e:
        logging.warning(f"newspaper3k extraction failed: {str(e)}")
    
    try:
        # Пробуем BeautifulSoup как запасной вариант
        soup = BeautifulSoup(html, 'html.parser')
        # Удаляем скрипты, стили и другой мусор
        for tag in soup(['script', 'style', 'meta', 'noscript']):
            tag.decompose()
        
        text = ' '.join(soup.stripped_strings)
        return text.strip()
    except Exception as e:
        logging.error(f"BeautifulSoup extraction failed: {str(e)}")
        return ""
