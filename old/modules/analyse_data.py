# modules/analyse_data.py

import os
import pandas as pd
import asyncio
import time
import logging
from modules.utils import load_role_description
from llm_clients import get_llm_client  # Импортируем функцию для получения LLM клиента

class RateLimiter:
    def __init__(self, max_rate, period=60):
        self.max_rate = max_rate
        self.period = period
        self.tokens = max_rate
        self.updated_at = time.monotonic()

    async def acquire(self):
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
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    # Путь к файлу с ролями
    role_file = os.path.join(roles_dir, 'prompt.txt')

    # Загрузка описания роли
    role_description = load_role_description(role_file)

    # Загрузка данных из CSV
    logging.info(f"Загрузка данных из {input_filename}...")
    df = pd.read_csv(input_filename)
    logging.info(f"Загружено {len(df)} строк.")

    # Если колонки 'analysis' нет, добавляем ее
    if 'analysis' not in df.columns:
        df['analysis'] = ""

    # Настройка LLM клиента на основе конфигурации
    provider = parser_config.get('provider', 'openai')  # По умолчанию OpenAI
    llm_client = get_llm_client(provider, parser_config)  # Передаём конфигурацию целиком

    # Ограничитель скорости и семафор
    max_rate = parser_config.get('rate_limit', 20)
    rate_limit_period = parser_config.get('rate_limit_period', 60)
    rate_limiter = RateLimiter(max_rate=max_rate, period=rate_limit_period)

    semaphore = asyncio.Semaphore(max_rate)

    async def process_row(index, row):
        try:
            if pd.isna(row['analysis']) or row['analysis'] == "":
                # Подготовка текста для анализа
                full_article_text = ""
                
                if 'Organization name' in row and pd.notna(row['Organization name']):
                    full_article_text += f"Company: {row['Organization name']}\n"
                
                if 'Website' in row and pd.notna(row['Website']):
                    full_article_text += f"Website: {row['Website']}\n"
                
                if pd.notna(row['description']):
                    full_article_text += str(row['description'])

                full_article_text = full_article_text.strip()

                if len(full_article_text) >= 100:
                    if len(full_article_text) > 5000:
                        full_article_text = full_article_text[:5000]
                    
                    messages = [
                        {"role": "system", "content": role_description},
                        {"role": "user", "content": full_article_text}
                    ]
                    
                    async with semaphore:
                        await rate_limiter.acquire()
                        response = await llm_client.get_completion(messages)
                    
                    df.at[index, 'analysis'] = response
                else:
                    logging.info(f"\nСтрока {index + 1}: текст слишком короткий для анализа.")
            else:
                logging.info(f"\nСтрока {index + 1}: анализ уже проведён.")
        
        except Exception as e:
            logging.error(f"\nОшибка при обработке строки {index + 1}: {e}")

        df.to_csv(output_filename, index=False)
        logging.info(f"Результаты сохранены в '{output_filename}'. Обработано {index + 1} строк.")

    tasks = [process_row(index, row) for index, row in df.iterrows()]
    await asyncio.gather(*tasks)

    logging.info("Анализ завершён.")

def run_analyse_data(input_filename, output_filename, roles_dir, parser_config):
    """Функция для запуска анализа данных."""
    if not asyncio.get_event_loop().is_running():
        asyncio.run(analyse_data(input_filename, output_filename, roles_dir, parser_config))
    else:
        return analyse_data(input_filename, output_filename, roles_dir, parser_config)
