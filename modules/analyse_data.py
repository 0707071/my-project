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
        self.max_rate = max_rate * 10
        self.period = period
        self.tokens = max_rate * 10
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

async def analyse_data(input_filename, output_filename, prompt_content, parser_config):
    """Асинхронно анализирует данные с помощью LLM."""
    try:
        # Загружаем данные
        df = pd.read_csv(input_filename)
        if df.empty:
            logging.warning("No data to analyze")
            return
        
        # Получаем LLM клиент
        llm_client = get_llm_client(
            model_name=parser_config.get('model', 'gpt-4o-mini'),
            config=parser_config
        )
        
        # Анализируем каждую статью
        for index, row in df.iterrows():
            try:
                if pd.isna(row['description']) or len(str(row['description'])) < 100:
                    df.at[index, 'analysis'] = "Error: Invalid content"
                    continue

                article_text = f"Title: {row['title']}\n\nContent: {row['description']}"
                messages = [
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": article_text}
                ]
                
                try:
                    response = await asyncio.wait_for(
                        llm_client.get_completion(messages),
                        timeout=60
                    )
                    df.at[index, 'analysis'] = response
                    logging.info(f"Analyzed article {index + 1}")
                except asyncio.TimeoutError:
                    df.at[index, 'analysis'] = "Error: Analysis timeout"
                    logging.warning(f"Timeout analyzing article {index + 1}")
                
                # Сохраняем каждые 3 статьи
                if (index + 1) % 3 == 0:
                    df.to_csv(output_filename, index=False)
            
            except Exception as e:
                logging.error(f"Error analyzing article {index}: {str(e)}")
                df.at[index, 'analysis'] = f"Error: {str(e)}"
                df.to_csv(output_filename, index=False)
        
        # Финальное сохранение
        df.to_csv(output_filename, index=False)
        
    except Exception as e:
        logging.error(f"Critical error in analysis: {str(e)}")
        raise

def run_analyse_data(input_filename, output_filename, prompt_content, parser_config):
    """Запускает анализ данных."""
    if not asyncio.get_event_loop().is_running():
        asyncio.run(analyse_data(input_filename, output_filename, prompt_content, parser_config))
    else:
        return analyse_data(input_filename, output_filename, prompt_content, parser_config)
