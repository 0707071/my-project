# Path: main.py
# This script is responsible for fetching articles from the internet, cleaning the data, 
# analyzing it using a language model (LLM), and exporting the results to Excel. 
# It manages the entire pipeline, from data retrieval to analysis.

import os
import json
import argparse
import asyncio
from datetime import datetime
import pandas as pd
import ast
from modules.fetch_data import fetch_and_save_articles
from modules.clean_data import clean_data
from modules.analyse_data import run_analyse_data  # Used to run data analysis
from modules.client_management import get_client_and_date
from modules.utils import load_config


def load_search_queries(roles_dir):
    """
    Load search queries from search_query.json.
    
    Args:
        roles_dir (str): Path to the directory containing search_query.json.
    
    Returns:
        tuple: A tuple containing queries, include, and exclude lists.
    """
    with open(os.path.join(roles_dir, 'search_query.json'), 'r') as f:
        search_queries = json.load(f)
    queries = search_queries['queries']
    include = search_queries['include']
    exclude = search_queries['exclude']
    return queries, include, exclude


def process_analysis(analysis_str):
    """
    Process a string representing analysis data.
    
    Args:
        analysis_str (str): A string representing the analysis.
    
    Returns:
        tuple: A tuple with processed analysis data.
    """
    try:
        analysis_list = ast.literal_eval(analysis_str)
        if len(analysis_list) >= 6:
            return analysis_list[0], analysis_list[1], analysis_list[2], \
                   analysis_list[3], analysis_list[4], analysis_list[5]
        else:
            return analysis_list[0] if len(analysis_list) > 0 else "", \
                   analysis_list[1] if len(analysis_list) > 1 else 0, \
                   analysis_list[2] if len(analysis_list) > 2 else "", \
                   analysis_list[3] if len(analysis_list) > 3 else [], \
                   analysis_list[4] if len(analysis_list) > 4 else "", \
                   analysis_list[5] if len(analysis_list) > 5 else ""
    except Exception:
        return "", 0, "", [], "", ""


async def export_to_excel(input_file, output_file):
    """
    Export processed data to an Excel file.
    
    Args:
        input_file (str): Path to the CSV file with processed data.
        output_file (str): Path to the output Excel file.
    """
    print("Exporting data to Excel...")
    df = pd.read_csv(input_file)
    df[['Company', 'Signal Strength', 'Time Frame', 'Key Phrases', 'Sales Team Notes', 'News Summary']] = \
        df['analysis'].apply(process_analysis).apply(pd.Series)
    df.to_excel(output_file, index=False)
    print(f"Data successfully exported to {output_file}")


async def fetch_data(client_name, config, queries, include, exclude, verbose, continue_from=None):
    """
    Asynchronously fetch data from an API and parse articles.
    
    Args:
        client_name (str): The name of the client for whom data is being fetched.
        config (dict): Configuration settings for the search.
        queries (list): List of search queries.
        include (list): Terms to include in the search.
        exclude (list): Terms to exclude from the search.
        verbose (bool): Whether to enable verbose output.
        continue_from (str, optional): Query to continue from if the process was interrupted.
    
    Returns:
        bool: True if data was fetched, False otherwise.
    """
    print("Starting data fetching and processing...")
    search_date_str = datetime.now().strftime('%Y-%m-%d')
    current_search_dir = os.path.join('results', client_name, search_date_str)
    os.makedirs(current_search_dir, exist_ok=True)
    results_file = os.path.join(current_search_dir, 'search_results.csv')

    start_index = 0
    if continue_from:
        start_index = queries.index(continue_from)
        print(f"Continuing from query: {continue_from}")

    for query in queries[start_index:]:
        print(f"Fetching data for query: {query}")
        await fetch_and_save_articles(query, include, exclude, config, results_file, verbose)
        await asyncio.sleep(2)  # Small delay between requests

    if os.path.exists(results_file) and os.path.getsize(results_file) > 0:
        df = pd.read_csv(results_file)
        print(f"Total articles fetched: {len(df)}")
        return True
    else:
        print("No articles were fetched. The results file was not created or is empty.")
        return False


async def main_async():
    """
    Main asynchronous function for the program. Manages data fetching, cleaning, and analysis.
    """
    parser = argparse.ArgumentParser(description="Signal Enricher")
    parser.add_argument('--fetch', action='store_true', help="Fetch data only")
    parser.add_argument('--clean', action='store_true', help="Clean data only")
    parser.add_argument('--analyze', action='store_true', help="Analyze data only")
    parser.add_argument('--continue_from', action='store_true', help="Continue from the last processed query")
    args = parser.parse_args()

    try:
        client_name, search_date = get_client_and_date()
        if client_name is None:
            return

        print(f"Client: {client_name}, Date: {search_date}")

        search_date_str = search_date.strftime('%Y-%m-%d')

        roles_dir = os.path.join('results', client_name, 'roles')
        queries, include, exclude = load_search_queries(roles_dir)

        config = load_config('config/search_config.json')
        verbose = config.get('verbose', False)

        if config.get('exclude_pdf', False):
            exclude += " -filetype:pdf"

        continue_from = None
        if args.continue_from:
            last_processed_query = input("Enter the last processed query: ")
            continue_from = next((q for q in queries if q.startswith(last_processed_query)), None)
            if continue_from:
                print(f"Continuing from query: {continue_from}")
            else:
                print("Query not found. Starting from the beginning.")

        data_fetched = False
        if args.fetch or not (args.clean or args.analyze):
            data_fetched = await fetch_data(client_name, config, queries, include, exclude, verbose, continue_from)

        file_path = os.path.join('results', client_name, search_date_str, 'search_results.csv')
        if (args.clean or not (args.fetch or args.analyze)) and (data_fetched or os.path.exists(file_path)):
            print("Starting data cleaning...")
            output_file = os.path.join('results', client_name, search_date_str, 'search_results_cleaned.csv')

            if os.path.getsize(file_path) > 0:
                try:
                    rows_before, rows_after = clean_data(file_path, output_file, verbose=True)
                    print(f"Data cleaning complete. Rows before: {rows_before}, after: {rows_after}")
                    print(f"Duplicates removed: {rows_before - rows_after}")
                except Exception as e:
                    print(f"Error during data cleaning: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"Warning: Input file {file_path} is empty. Data cleaning skipped.")
        elif not data_fetched:
            print("Skipping cleaning step as no data was fetched.")

        cleaned_file = os.path.join('results', client_name, search_date_str, 'search_results_cleaned.csv')
        analysed_file = os.path.join('results', client_name, search_date_str, 'search_results_analysed.csv')
        if (args.analyze or not (args.fetch or args.clean)) and (data_fetched or os.path.exists(cleaned_file)):
            print("Starting data analysis...")
            await run_analyse_data(cleaned_file, analysed_file, roles_dir, config)
            print("Data analysis complete.")

            # Export to Excel
            excel_file = os.path.join('results', client_name, search_date_str, f"{client_name}_{search_date_str}.xlsx")
            await export_to_excel(analysed_file, excel_file)
        elif not data_fetched:
            print("Skipping analysis step as no data was fetched.")

        print("Program finished successfully.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """
    Wrapper to run the asynchronous main function.
    """
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
