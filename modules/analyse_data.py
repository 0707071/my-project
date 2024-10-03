# Path: modules/analyse_data.py
# This file analyzes the fetched articles using a language model (LLM). It processes each article 
# and generates analysis based on the specified role description.

import os
import pandas as pd
import asyncio
import time
import logging
from modules.utils import load_role_description
from llm_clients import get_llm_client  # Import function to get LLM client

class RateLimiter:
    """
    A class to implement rate limiting for API requests.
    Controls the rate of requests to prevent exceeding API limits.
    """
    def __init__(self, max_rate, period=60):
        self.max_rate = max_rate
        self.period = period
        self.tokens = max_rate
        self.updated_at = time.monotonic()

    async def acquire(self):
        """
        Acquires a token for making an API request. If tokens are not available, it waits.
        """
        while True:
            now = time.monotonic()
            time_passed = now - self.updated_at
            self.tokens += time_passed * (self.max_rate / self.period)
            if self.tokens > self.max_rate:
                self.tokens = self.max_rate
            self.updated_at = now

            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            sleep_time = (1 - self.tokens) / (self.max_rate / self.period)
            await asyncio.sleep(sleep_time)

async def analyse_data(input_filename, output_filename, roles_dir, parser_config):
    """
    Asynchronously analyzes data using a language model (LLM).

    Args:
        input_filename (str): Path to the input CSV file with article data.
        output_filename (str): Path to the output CSV file to save the analysis results.
        roles_dir (str): Path to the directory containing role descriptions for analysis.
        parser_config (dict): Configuration for LLM and analysis settings.

    Returns:
        None
    """
    # Setting up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    # Path to the file with role description
    role_file = os.path.join(roles_dir, 'prompt.txt')

    # Load role description
    role_description = load_role_description(role_file)

    # Load data from CSV
    logging.info(f"Loading data from {input_filename}...")
    df = pd.read_csv(input_filename)
    logging.info(f"Loaded {len(df)} rows.")

    # Add 'analysis' column if not present
    if 'analysis' not in df.columns:
        df['analysis'] = ""

    # Configure LLM client based on parser configuration
    provider = parser_config.get('provider', 'openai')  # Default to OpenAI
    llm_client = get_llm_client(provider, parser_config)  # Pass the entire configuration

    # Rate limiter and semaphore for controlling request rate
    max_rate = parser_config.get('rate_limit', 20)
    rate_limit_period = parser_config.get('rate_limit_period', 60)
    rate_limiter = RateLimiter(max_rate=max_rate, period=rate_limit_period)

    semaphore = asyncio.Semaphore(max_rate)

    async def process_row(index, row):
        """
        Processes a single row from the dataframe, sends it to the LLM for analysis.

        Args:
            index (int): Index of the row.
            row (pd.Series): Row data to be processed.

        Returns:
            None
        """
        try:
            if pd.isna(row['analysis']) or row['analysis'] == "":
                # Prepare text for analysis
                full_article_text = ""
                
                if 'Organization name' in row and pd.notna(row['Organization name']):
                    full_article_text += f"Company: {row['Organization name']}\n"
                
                if 'Website' in row and pd.notna(row['Website']):
                    full_article_text += f"Website: {row['Website']}\n"
                
                if pd.notna(row['description']):
                    full_article_text += str(row['description'])

                full_article_text = full_article_text.strip()

                # Only analyze if the article text is long enough
                if len(full_article_text) >= 100:
                    if len(full_article_text) > 5000:
                        full_article_text = full_article_text[:5000]
                    
                    # Prepare messages for the LLM
                    messages = [
                        {"role": "system", "content": role_description},
                        {"role": "user", "content": full_article_text}
                    ]
                    
                    async with semaphore:
                        await rate_limiter.acquire()  # Ensure rate limit compliance
                        response = await llm_client.get_completion(messages)
                    
                    # Store the analysis in the dataframe
                    df.at[index, 'analysis'] = response
                else:
                    logging.info(f"\nRow {index + 1}: text too short for analysis.")
            else:
                logging.info(f"\nRow {index + 1}: analysis already performed.")
        
        except Exception as e:
            logging.error(f"\nError processing row {index + 1}: {e}")

        # Save results after processing each row
        df.to_csv(output_filename, index=False)
        logging.info(f"Results saved to '{output_filename}'. Processed {index + 1} rows.")

    # Create tasks for each row and execute them asynchronously
    tasks = [process_row(index, row) for index, row in df.iterrows()]
    await asyncio.gather(*tasks)

    logging.info("Analysis completed.")

def run_analyse_data(input_filename, output_filename, roles_dir, parser_config):
    """
    Function to start data analysis. It runs the analysis in an asynchronous loop.

    Args:
        input_filename (str): Path to the input CSV file.
        output_filename (str): Path to the output CSV file to save the results.
        roles_dir (str): Directory containing role description files.
        parser_config (dict): Configuration settings for the parser.

    Returns:
        None
    """
    if not asyncio.get_event_loop().is_running():
        asyncio.run(analyse_data(input_filename, output_filename, roles_dir, parser_config))
    else:
        return analyse_data(input_filename, output_filename, roles_dir, parser_config)
