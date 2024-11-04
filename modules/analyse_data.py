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
    Асинхронно анализирует данные с помощью LLM.
    """
    # Загружаем промпт
    prompt_file = os.path.join(roles_dir, 'prompt.txt')
    if not os.path.exists(prompt_file):
        raise ValueError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r') as f:
        prompt_content = f.read()
        print(f"Using prompt:\n{prompt_content[:200]}...")
    
    # Загружаем данные
    df = pd.read_csv(input_filename)
    print(f"Loaded {len(df)} articles for analysis")
    
    # Получаем LLM клиент
    llm_client = get_llm_client('openai', parser_config)
    
    # Анализируем каждую статью
    for index, row in df.iterrows():
        try:
            # Подготавливаем текст для анализа
            article_text = f"Title: {row['title']}\n\nContent: {row['description']}"
            
            # Формируем сообщения для LLM
            messages = [
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": article_text}
            ]
            
            # Получаем ответ от LLM
            response = await llm_client.get_completion(messages)
            print(f"Got analysis for article {index + 1}/{len(df)}")
            print(f"Analysis: {response[:200]}...")
            
            # Сохраняем анализ
            df.at[index, 'analysis'] = response
            
            # Периодически сохраняем результаты
            if (index + 1) % 10 == 0:
                df.to_csv(output_filename, index=False)
                print(f"Saved progress: {index + 1} articles analyzed")
        
        except Exception as e:
            print(f"Error analyzing article {index + 1}: {str(e)}")
            df.at[index, 'analysis'] = f"Error: {str(e)}"
    
    # Сохраняем финальные результаты
    df.to_csv(output_filename, index=False)
    print("Analysis completed and saved")

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
