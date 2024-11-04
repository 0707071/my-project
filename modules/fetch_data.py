# Path: modules/fetch_data.py
# This file retrieves data from search engines and downloads articles from webpages.

import os
import asyncio
import aiohttp
import pandas as pd
import time
import xml.etree.ElementTree as ET
from newspaper import Article
from modules.date_utils import parse_date
from datetime import datetime, timedelta

# Получаем данные для авторизации из переменных окружения
XMLSTOCK_USER = os.getenv("XMLSTOCK_USER")
XMLSTOCK_KEY = os.getenv("XMLSTOCK_KEY")
XMLSTOCK_URL = "https://xmlstock.com/google/xml/"

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


async def fetch_and_parse(url, verbose=False, proxy=None, timeout=240):
    """
    Асинхронно получает и парсит статью по указанному URL.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    print(f"\nFetching article: {url}")
    
    async with semaphore:
        try:
            # Увеличиваем количество попыток подключения
            for attempt in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as response:
                            print(f"Response status: {response.status}")
                            # Проверяем Content-Type
                            content_type = response.headers.get('Content-Type', '').lower()
                            if 'pdf' in content_type or 'application/octet-stream' in content_type:
                                print(f"Skipping PDF or binary content: {url}")
                                return None
                            
                            if response.status != 200:
                                raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status)
                            
                            html_content = await response.text()
                            print(f"Received HTML content length: {len(html_content)}")
                            
                            if len(html_content) < 1000:  # Проверяем минимальный размер контента
                                print(f"Content too short, skipping: {len(html_content)} bytes")
                                return None
                            
                            article = Article(url)
                            article.set_html(html_content)
                            article.parse()
                            
                            text = article.text
                            if len(text) < 200:  # Проверяем минимальную длину текста
                                print(f"Parsed text too short, skipping: {len(text)} chars")
                                return None
                            
                            print(f"Parsed article title: {article.title}")
                            print(f"Parsed article text (first 200 chars): {text[:200]}...")
                            print(f"Total text length: {len(text)}")
                            
                            return {
                                'title': article.title,
                                'authors': article.authors,
                                'text': text,
                                'article_url': url
                            }
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == 2:  # Последняя попытка
                        raise
                    await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка между попытками
                    
        except Exception as e:
            print(f"Error fetching or parsing article: {url}")
            print(f"Error details: {str(e)}")
            print(f"Full error: {repr(e)}")
            return None
        finally:
            await asyncio.sleep(REQUEST_DELAY)


async def process_search_results(search_results, verbose=False, proxy=None):
    """
    Асинхронно обрабатывает результаты поиска, получая и парся статьи.
    """
    tasks = []
    for result in search_results:
        task = asyncio.create_task(fetch_and_parse(result['link'], verbose, proxy))
        tasks.append(task)
    
    return await asyncio.gather(*tasks)


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
