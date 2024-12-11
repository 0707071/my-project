# Path: modules/fetch_company_data.py
# This script is responsible for fetching company data based on search queries
# from an input file (Excel or CSV), and saving the enriched results to an output CSV.

import pandas as pd
import asyncio
import csv
import os
import logging
from modules.fetch_data import fetch_xmlstock_search_results, process_search_results
from modules.utils import clean_domain

MAX_CONCURRENT_REQUESTS = 20  # Maximum number of concurrent requests
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

def setup_logging():
    """
    Configures logging to display messages in the console.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )

async def fetch_company_data(input_file, output_file, config):
    """
    Asynchronously fetches company data based on search queries from an input file.

    Args:
        input_file (str): Path to the input Excel or CSV file.
        output_file (str): Path to save the output enriched data as CSV.
        config (dict): Configuration dictionary containing search settings.
    """
    try:
        # Attempt to load the input data
        try:
            df = pd.read_excel(input_file, engine='openpyxl')
            logging.info(f"Successfully loaded {len(df)} rows from Excel file.")
        except Exception:
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
                logging.info(f"Successfully loaded {len(df)} rows from UTF-8 CSV file.")
            except Exception:
                df = pd.read_csv(input_file, encoding='latin1')
                logging.info(f"Successfully loaded {len(df)} rows from Latin-1 CSV file.")
        
        logging.info(f"Input file columns: {df.columns.tolist()}")
    except Exception as e:
        logging.error(f"Error reading input file: {str(e)}")
        return

    search_column = config['search_column']
    search_queries = config['search_queries']
    use_domain = config.get('use_domain', False)
    company_name_column = config['company_name_column']

    # Verify required columns
    required_columns = [company_name_column, search_column, 'Organization description']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logging.error(f"Missing columns in input file: {', '.join(missing_columns)}")
        raise ValueError(f"Missing required columns in input file: {', '.join(missing_columns)}")

    results = []

    # Function to save results to CSV
    def save_results(results, output_file, mode='w'):
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_file, mode=mode, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
        logging.info(f"Data saved to file {output_file}")

    # Asynchronous function to process a single company
    async def process_company(index, row):
        company_name = row[company_name_column]
        search_value = row[search_column]

        if pd.isna(search_value):
            logging.info(f"Skipping company '{company_name}': No search value.")
            return []

        if use_domain:
            search_value = clean_domain(str(search_value))
            search_prefix = f"site:{search_value}"
        else:
            search_prefix = str(search_value)

        company_results = []

        # Perform searches for the company based on configured search queries
        for query in search_queries:
            full_query = f"{search_prefix} {query}"
            logging.info(f"Executing search for company '{company_name}': '{full_query}'")

            async with semaphore:
                search_results = await fetch_xmlstock_search_results(full_query, "", "", config)
                if search_results:
                    logging.info(f"Search results: {search_results}")
                else:
                    logging.info(f"No results found for: {full_query}")

                if search_results:
                    articles = await process_search_results(search_results)
                    if articles:
                        article = articles[0]  # Only take the first result for each query
                        result = row.to_dict()
                        result.update({
                            'company_name': company_name,
                            'search_query': full_query,
                            'title': article.get('title', ''),
                            'link': article.get('article_url', ''),
                            'found_text': article.get('text', '')[:1000],
                            'description': article.get('text', '')[:5000]
                        })
                        company_results.append(result)
                        logging.info(f"Results for company '{company_name}': {result}")
                        break  # Stop after the first successful result

            # Add delay between queries as configured
            await asyncio.sleep(config.get('delay_between_queries', 1))

        # If no results, create an empty result entry
        if not company_results:
            result = row.to_dict()
            result.update({
                'company_name': company_name,
                'search_query': '',
                'title': '',
                'link': '',
                'found_text': '',
                'description': ''
            })
            company_results.append(result)

        return company_results

    # Process all companies asynchronously
    tasks = [process_company(index, row) for index, row in df.iterrows()]
    for task_batch in asyncio.as_completed(tasks, timeout=60):
        try:
            company_results = await task_batch
            results.extend(company_results)

            # Save intermediate results after processing 10 companies
            if len(results) >= 10:
                save_results(results, output_file, mode='a')
                results.clear()
        except asyncio.TimeoutError:
            logging.error(f"Timeout occurred for one of the companies")

    # Save any remaining results
    if results:
        save_results(results, output_file, mode='a')

    logging.info(f"Data processing completed.")

def run_fetch_company_data(input_file, output_file, config):
    """
    Entry point to start fetching company data based on the input file.

    Args:
        input_file (str): Path to the input Excel or CSV file.
        output_file (str): Path to save the output enriched data as CSV.
        config (dict): Configuration dictionary containing search settings.
    """
    setup_logging()  # Set up logging
    asyncio.run(fetch_company_data(input_file, output_file, config))  # Run the async task
