import asyncio
import aiohttp
import pandas as pd
import time
import xml.etree.ElementTree as ET
from newspaper import Article
from config.api_keys import api_keys
from modules.date_utils import parse_date
from datetime import datetime, timedelta
import os

# Данные для авторизации в API
user = api_keys["xmlstock_user"]
key = api_keys["xmlstock_key"]
url = "https://xmlstock.com/google/xml/"

# Задержка между запросами в секундах
REQUEST_DELAY = 0.5

async def fetch_xmlstock_search_results(query, include, exclude, config, verbose=False):
    """
    Асинхронно получает результаты поиска из API xmlstock.
    """
    results = []
    
    full_query = query
    if include:
        full_query += f" {include}"
    if exclude:
        full_query += f" {exclude}"
    
    print(f"Полный поисковый запрос: {full_query}")
    
    xmlsearch_config = next((engine for engine in config['search_engines'] if engine['name'] == 'xmlsearch'), None)
    if not xmlsearch_config:
        print("Конфигурация для xmlsearch не найдена")
        return results

    params = {
        "user": user,
        "key": key,
        "query": full_query,
        "groupby": min(max(config['num_results'], 10), 100),
        "sort": "date"
    }
    
    # Добавляем параметры из конфигурации
    for param in ['domain', 'tbm', 'hl', 'device', 'lr']:
        if xmlsearch_config.get(param):
            params[param] = xmlsearch_config[param]
    
    if config['days']:
        params["tbs"] = f"qdr:d{config['days']}"
    
    async with aiohttp.ClientSession() as session:
        for page in range(config['num_pages']):
            params['page'] = page
            if verbose:
                print(f"Отправка запроса с параметрами: {params}")
            
            async with session.get(url, params=params, timeout=30) as response:
                if verbose:
                    print(f"Код статуса ответа: {response.status}")
                    print(f"URL запроса: {response.url}")
                
                if response.status != 200:
                    if verbose:
                        print(f"Ошибка при получении результатов: {response.status}")
                        print(await response.text())
                    continue

                content = await response.text()
                root = ET.fromstring(content)
                for group in root.findall('.//group'):
                    for doc in group.findall('doc'):
                        pub_date = doc.find('pubDate').text if doc.find('pubDate') is not None else "N/A"
                        result = {
                            'title': doc.find('title').text if doc.find('title') is not None else "N/A",
                            'link': doc.find('url').text if doc.find('url') is not None else "N/A",
                            'pubDate': pub_date
                        }
                        results.append(result)
                
                if verbose:
                    print(f"Получено результатов: {len(results)}")
            
            await asyncio.sleep(REQUEST_DELAY)  # Добавляем задержку между запросами

    print(f"Всего найдено ссылок: {len(results)}")
    return results

async def fetch_and_parse(url, verbose=False, proxy=None, timeout=240):
    """
    Асинхронно получает и парсит статью по указанному URL.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    start_time = time.monotonic()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as response:
                if response.status != 200:
                    raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status)
                html_content = await response.text()
        
        article = Article(url)
        article.set_html(html_content)
        article.parse()
        print(f"Успешно получен текст статьи {article.text[:500]}")
        return {
            'title': article.title,
            'authors': article.authors,
            'text': article.text,
            'article_url': url
        }
    except asyncio.TimeoutError:
        print(f"Таймаут при получении статьи: {url}")
        return None
    except Exception as e:
        print(f"Ошибка при получении или парсинге статьи: {url}\n{e}")
        return None
    finally:
        end_time = time.monotonic()
        print(f"Время выполнения запроса для {url}: {end_time - start_time:.2f} секунд")

async def process_search_results(search_results, verbose=False, proxy=None):
    """
    Асинхронно обрабатывает результаты поиска, получая и парся статьи.
    """
    tasks = [asyncio.create_task(fetch_and_parse(result['link'], verbose, proxy)) for result in search_results]
    
    processed_articles = []
    successful_parses = 0
    failed_parses = 0
    
    for task in asyncio.as_completed(tasks):
        try:
            result = await asyncio.wait_for(task, timeout=300)
            if result:
                processed_articles.append(result)
                successful_parses += 1
            else:
                failed_parses += 1
        except asyncio.TimeoutError:
            print("Таймаут задачи, переход к следующей.")
            failed_parses += 1
        except Exception as e:
            print(f"Ошибка при выполнении задачи: {e}")
            failed_parses += 1
    
    print(f"Успешно спарсено статей: {successful_parses}")
    print(f"Не удалось спарсить статей: {failed_parses}")
    
    return processed_articles

async def fetch_and_save_articles(query, include, exclude, config, output_filename, verbose=False, proxy=None):
    """
    Асинхронно получает результаты поиска, обрабатывает их и сохраняет список статей.
    """
    search_results = await fetch_xmlstock_search_results(query, include, exclude, config, verbose)
    if not search_results:
        print("Результаты поиска не найдены.")
        return []

    articles = await process_search_results(search_results, verbose, proxy)
    
    processed_articles = []
    for search_result, article in zip(search_results, articles):
        if article:
            processed_article = {
                'title': search_result.get('title', ''),
                'link': search_result.get('link', ''),
                'pubDate': search_result.get('pubDate', ''),
                'description': article.get('text', '')[:500],
                'query': query,
                'analysis': ''
            }
            processed_articles.append(processed_article)

    # Сохраняем результаты после обработки всего поискового запроса
    df = pd.DataFrame(processed_articles)
    if os.path.exists(output_filename):
        df.to_csv(output_filename, mode='a', header=False, index=False)
    else:
        df.to_csv(output_filename, index=False)

    print(f"Сохранено {len(processed_articles)} статей для запроса: {query}")
    return processed_articles

async def fetch_data(client_name, config, queries, include, exclude, verbose, continue_from=None):
    """Асинхронно получает данные из API xmlstock и парсит статьи."""
    print("Начинаем получение и обработку данных...")
    search_date_str = datetime.now().strftime('%Y-%m-%d')
    current_search_dir = os.path.join('results', client_name, search_date_str)
    os.makedirs(current_search_dir, exist_ok=True)
    results_file = os.path.join(current_search_dir, 'search_results.csv')

    start_index = 0
    if continue_from:
        start_index = queries.index(continue_from)
        print(f"Продолжаем с запроса: {continue_from}")

    all_processed_articles = []
    for query in queries[start_index:]:
        print(f"Получаем данные для запроса: {query}")
        processed_articles = await fetch_and_save_articles(query, include, exclude, config, results_file, verbose)
        all_processed_articles.extend(processed_articles)

    if all_processed_articles:
        print(f"Всего получено и обработано статей: {len(all_processed_articles)}")
        return True
    else:
        print("Статьи не были получены.")
        return False

def save_results_to_csv(results, output_filename, verbose=False):
    """
    Сохраняет результаты в CSV файл.
    """
    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_filename, index=False)
        if verbose:
            print(f"Извлеченные статьи сохранены в '{output_filename}'")
    else:
        if verbose:
            print("Статьи не были извлечены.")
