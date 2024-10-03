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

# Authorization data from environment variables
user = os.getenv("XMLSTOCK_USER", "")
key = os.getenv("XMLSTOCK_KEY", "")
url = "https://xmlstock.com/google/xml/"

# Semaphore to limit the number of concurrent requests
MAX_CONCURRENT_REQUESTS = 10
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# Delay between requests in seconds
REQUEST_DELAY = 1


async def fetch_xmlstock_search_results(query, include, exclude, config, verbose=False):
    """
    Asynchronously fetches search results from the xmlstock API.
    
    Args:
        query (str): The search query.
        include (str): Additional terms to include in the search.
        exclude (str): Terms to exclude from the search.
        config (dict): Configuration settings for the search.
        verbose (bool, optional): If True, prints detailed output. Default is False.
    
    Returns:
        list: List of search results.
    """
    results = []
    
    full_query = query
    if include:
        full_query += f" {include}"
    if exclude:
        full_query += f" {exclude}"
    
    print(f"Full search query: {full_query}")
    
    xmlsearch_config = next((engine for engine in config['search_engines'] if engine['name'] == 'xmlsearch'), None)
    if not xmlsearch_config:
        print("Configuration for xmlsearch not found.")
        return results

    params = {
        "user": user,
        "key": key,
        "query": full_query,
        "groupby": min(max(config['num_results'], 10), 100),
        "sort": "date"
    }
    
    # Add additional parameters from the config
    for param in ['domain', 'tbm', 'hl', 'device', 'lr']:
        if xmlsearch_config.get(param):
            params[param] = xmlsearch_config[param]
    
    if config['days']:
        params["tbs"] = f"qdr:d{config['days']}"
    
    async with aiohttp.ClientSession() as session:
        for page in range(config['num_pages']):
            params['page'] = page
            if verbose:
                print(f"Sending request with params: {params}")
            
            async with semaphore:  # Using semaphore to limit concurrent requests
                try:
                    async with session.get(url, params=params, timeout=30) as response:
                        if verbose:
                            print(f"Response status code: {response.status}")
                            print(f"Request URL: {response.url}")
                        
                        if response.status != 200:
                            if verbose:
                                print(f"Error fetching results: {response.status}")
                                print(await response.text())
                            continue

                        content = await response.text()
                        root = ET.fromstring(content)
                        for group in root.findall('.//group'):
                            for doc in group.findall('doc'):
                                pub_date = doc.find('pubDate').text if doc.find('pubDate') is not None else "N/A"
                                pub_date_dt = parse_date(pub_date) if pub_date != "N/A" else None
                                result = {
                                    'title': doc.find('title').text if doc.find('title') is not None else "N/A",
                                    'link': doc.find('url').text if doc.find('url') is not None else "N/A",
                                    'pubDate': pub_date
                                }
                                results.append(result)
                                if len(results) >= config['num_results']:
                                    return results[:config['num_results']]
                    
                    if verbose:
                        print(f"Results fetched: {len(results)}")
                
                except asyncio.TimeoutError:
                    if verbose:
                        print(f"Timeout fetching results for page {page}")
                except Exception as e:
                    if verbose:
                        print(f"Error fetching results for page {page}: {e}")
                
                await asyncio.sleep(REQUEST_DELAY)  # Adding delay between requests

    return results[:config['num_results']]


async def fetch_and_parse(url, verbose=False, proxy=None, timeout=240):
    """
    Asynchronously fetches and parses an article from the given URL.
    
    Args:
        url (str): The article URL.
        verbose (bool, optional): If True, prints detailed output. Default is False.
        proxy (str, optional): Proxy URL if needed. Default is None.
        timeout (int, optional): Timeout for fetching the article. Default is 240 seconds.
    
    Returns:
        dict: Parsed article data including title, authors, and text.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    async with semaphore:  # Using semaphore to limit concurrent requests
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as response:
                    if response.status != 200:
                        raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status)
                    html_content = await response.text()
            
            article = Article(url)
            article.set_html(html_content)
            article.parse()
            print(f"Successfully fetched article text: {article.text[:500]}")
            return {
                'title': article.title,
                'authors': article.authors,
                'text': article.text,
                'article_url': url
            }
        except asyncio.TimeoutError:
            print(f"Timeout fetching article: {url}")
            return {
                'title': "N/A",
                'authors': [],
                'text': "Timeout fetching article",
                'article_url': url
            }
        except Exception as e:
            print(f"Error fetching or parsing article: {url}\n{e}")
            return {
                'title': "N/A",
                'authors': [],
                'text': f"Error: {str(e)}",
                'article_url': url
            }
        finally:
            await asyncio.sleep(REQUEST_DELAY)  # Adding delay between requests


async def process_search_results(search_results, verbose=False, proxy=None):
    """
    Asynchronously processes search results by fetching and parsing articles.
    
    Args:
        search_results (list): List of search result links to process.
        verbose (bool, optional): If True, prints detailed output. Default is False.
        proxy (str, optional): Proxy URL if needed. Default is None.
    
    Returns:
        list: List of parsed article data.
    """
    tasks = [fetch_and_parse(result['link'], verbose, proxy) for result in search_results]
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
