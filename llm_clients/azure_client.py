# Path: llm_clients/azure_client.py
# This file defines the client for interacting with Azure OpenAI API.

import os
import asyncio
import logging
import aiohttp
import json
from typing import List, Dict, Any, Callable, AsyncGenerator
from .base_client import BaseLLMClient


class AzureOpenAIClient(BaseLLMClient):
    """
    Client for interacting with the Azure OpenAI API.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the Azure OpenAI client with configuration settings.

        Args:
            config (Dict[str, Any]): Configuration settings for the client.
        """
        self.config = config
        
        # Базовая модель, которую мы используем - только gpt-4o-mini
        self.model = config.get('model', 'gpt-4o-mini')
        
        # ВАЖНО: Проверяем, что использована правильная модель
        if self.model != 'gpt-4o-mini':
            raise ValueError(f"Модель {self.model} не разрешена. Используйте только gpt-4o-mini")
        
        # Azure specific settings
        self.endpoint = config.get('endpoint', os.getenv('AZURE_OPENAI_ENDPOINT'))
        self.api_key = config.get('api_key', os.getenv('AZURE_OPENAI_API_KEY'))
        self.api_version = config.get('api_version', os.getenv('AZURE_OPENAI_API_VERSION', '2024-08-01-preview'))
        
        # Настроим деплойменты для конкретных моделей
        self.deployment_mapping = {
            'gpt-4o': os.getenv('AZURE_OPENAI_DEPLOYMENT_4O', 'gpt-4o'),
            'gpt-4o-mini': os.getenv('AZURE_OPENAI_DEPLOYMENT_4O_MINI', 'gpt-4o-mini')
        }
        
        # Выбираем правильный деплоймент для используемой модели
        self.deployment = self.deployment_mapping.get(self.model)
        
        # Конфигурация retry и таймауты
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1)
        self.timeout = config.get('timeout', 60)
        
        # Проверка наличия необходимых параметров
        if not self.endpoint or not self.api_key:
            raise ValueError("Не указаны endpoint или API ключ для Azure OpenAI")
        
        if not self.deployment:
            raise ValueError(f"Не найден deployment для модели {self.model}")
        
        logging.info(f"Инициализирован клиент Azure OpenAI с моделью {self.model}, deployment {self.deployment}")

    def _get_headers(self):
        """Возвращает заголовки для запроса к Azure OpenAI API."""
        return {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }

    def _get_api_url(self):
        """Возвращает URL для API запроса к Azure OpenAI."""
        return f"{self.endpoint}openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"

    async def _handle_api_call(self, api_call):
        """
        Обрабатывает API вызовы с повторными попытками.
        """
        for attempt in range(self.max_retries):
            try:
                return await api_call()
            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # Rate limit
                    logging.warning(f"Достигнут лимит запросов (попытка {attempt + 1})")
                elif e.status == 401:  # Unauthorized
                    logging.error(f"Ошибка авторизации API: {str(e)}")
                    raise  # Сразу выбрасываем, не пытаемся повторить
                else:
                    logging.error(f"Ошибка API (попытка {attempt + 1}): {str(e)}")
                
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                logging.error(f"Неожиданная ошибка (попытка {attempt + 1}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def get_completion(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> str:
        """
        Получает завершение от Azure OpenAI API.
        
        Args:
            messages (List[Dict[str, str]]): Список сообщений для отправки модели.
            update_callback (Callable[[], Any], optional): Колбэк-функция для обновления статуса.
        
        Returns:
            str: Ответ от языковой модели.
        """
        async def api_call():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._get_api_url(),
                    headers=self._get_headers(),
                    json={
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 4000,
                        "top_p": 0.95,
                        "frequency_penalty": 0,
                        "presence_penalty": 0
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data['choices'][0]['message']['content']

        result = await self._handle_api_call(api_call)
        if update_callback:
            await update_callback()
        return result

    async def get_completion_stream(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> AsyncGenerator[str, None]:
        """
        Получает потоковое завершение от Azure OpenAI API.
        
        Args:
            messages (List[Dict[str, str]]): Список сообщений для отправки модели.
            update_callback (Callable[[], Any], optional): Колбэк-функция для обновления статуса.
        
        Yields:
            str: Фрагменты ответа от языковой модели.
        """
        async def api_call():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._get_api_url(),
                    headers=self._get_headers(),
                    json={
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 4000,
                        "top_p": 0.95,
                        "frequency_penalty": 0,
                        "presence_penalty": 0,
                        "stream": True
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    response.raise_for_status()
                    
                    # Обработка потокового ответа
                    async for line in response.content:
                        line = line.strip()
                        if not line or line == b'data: [DONE]':
                            continue
                        
                        if line.startswith(b'data: '):
                            try:
                                data = json.loads(line[6:])  # Пропускаем 'data: '
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        yield delta['content']
                            except Exception as e:
                                logging.error(f"Ошибка при анализе потокового ответа: {str(e)}")

        async for chunk in await self._handle_api_call(api_call):
            if update_callback:
                await update_callback()
            yield chunk 