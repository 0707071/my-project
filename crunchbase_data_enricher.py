# Path: crunchbase_data_enricher.py
# This script handles data enrichment from Crunchbase exports.
# It fetches company data and runs analysis on it, saving the results to CSV files.

import os
import argparse
from datetime import datetime
from modules.fetch_company_data import run_fetch_company_data
from modules.analyse_data import run_analyse_data
from modules.client_management import get_client_and_date
from modules.utils import load_config
import logging

def setup_logging():
    """
    Sets up logging configuration to output log messages to the console.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def main():
    """
    Main function to fetch and analyze company data from Crunchbase exports.
    It supports two actions: fetching data and analyzing data, based on command-line arguments.
    """
    setup_logging()  # Set up logging
    parser = argparse.ArgumentParser(description="Company data enrichment")
    parser.add_argument('--fetch', action='store_true', help="Fetch data only")
    parser.add_argument('--analyze', action='store_true', help="Analyze data only")
    args = parser.parse_args()

    try:
        # Retrieve client name and current date
        client_name, search_date = get_client_and_date()
        if client_name is None:
            logging.error("Client not found. Exiting.")
            return

        logging.info(f"Client: {client_name}, Date: {search_date}")

        # Format date for use in file paths
        search_date_str = search_date.strftime('%Y-%m-%d')

        # Load the configuration file
        config_path = os.path.join('results', client_name, 'roles', 'config.json')
        if not os.path.exists(config_path):
            logging.error(f"Configuration file {config_path} not found.")
            return

        config = load_config(config_path)

        # Define input, fetched, and analyzed file paths
        input_file = os.path.join('results', client_name, search_date_str, config['input_file'])
        if not os.path.exists(input_file):
            logging.error(f"Input file {input_file} not found.")
            return

        fetched_file = os.path.join('results', client_name, search_date_str, 'fetched_company_data.csv')
        analyzed_file = os.path.join('results', client_name, search_date_str, 'analyzed_data.csv')

        # Fetch data from Crunchbase if --fetch is specified or --analyze is not provided
        if args.fetch or not args.analyze:
            logging.info("Starting data fetch...")
            run_fetch_company_data(input_file, fetched_file, config)
            if not os.path.exists(fetched_file):
                logging.error(f"Error: Fetched data file {fetched_file} was not created.")
                return
            logging.info(f"Data fetched and saved to {fetched_file}")

        # Analyze the fetched data if --analyze is specified or --fetch is not provided
        if args.analyze or not args.fetch:
            logging.info("Starting data analysis...")
            if not os.path.exists(fetched_file):
                logging.error(f"Error: Fetched data file {fetched_file} does not exist.")
                return

            logging.info(f"Using configuration for analysis: {config}")
            run_analyse_data(fetched_file, analyzed_file, os.path.join('results', client_name, 'roles'), config)
            if not os.path.exists(analyzed_file):
                logging.error(f"Error: Analyzed data file {analyzed_file} was not created.")
                return
            logging.info(f"Data analyzed and saved to {analyzed_file}")

        logging.info("Program finished successfully.")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
