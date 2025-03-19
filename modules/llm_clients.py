import openai
import aiohttp
import os
import json
import asyncio
import logging
from typing import Dict, Any, List

# ВАЖНО: В проекте используется только модель gpt-4o-mini
# Не заменять на gpt-4, gpt-4-turbo или другие модели без явного разрешения техлида
# Это критично для контроля расходов

# SDK Azure OpenAI недоступен
AZURE_SDK_AVAILABLE = False

class ModelError(Exception):
    """Исключение при попытке использовать неразрешенную модель"""
    pass

def validate_model(model: str) -> None:
    """
    Проверяет, что используется разрешенная модель.
    ВАЖНО: Единственная разрешенная модель - gpt-4o-mini
    """
    ALLOWED_MODEL = 'gpt-4o-mini'
    if model != ALLOWED_MODEL:
        raise ModelError(
            f"Попытка использовать неразрешенную модель: {model}. "
            f"Разрешена только модель {ALLOWED_MODEL}. "
            "Использование других моделей запрещено для контроля расходов."
        )

def get_llm_client(model_name: str, config: Dict[str, Any], provider: str = 'azure') -> Any:
    """
    Factory function для получения LLM клиента.
    По умолчанию использует Azure OpenAI.
    
    Args:
        model_name (str): Название модели (всегда должно быть 'gpt-4o-mini')
        config (Dict[str, Any]): Конфигурация клиента
        provider (str): Провайдер API ('azure' или 'openai'), по умолчанию 'azure'
    
    Returns:
        Any: Клиент для выбранного провайдера
    """
    # ВАЖНО: Проверяем модель при создании клиента
    validate_model(model_name)
    
    # Выбираем клиента в зависимости от провайдера
    if provider.lower() == 'openai':
        return OpenAIClient(config, model_name)
    elif provider.lower() == 'azure':
        return AzureOpenAIClient(config, model_name)
    else:
        raise ValueError(f"Неизвестный провайдер: {provider}. Доступны: 'azure', 'openai'")

class OpenAIClient:
    def __init__(self, config: Dict[str, Any], model_name: str = 'gpt-4o-mini'):
        # ВАЖНО: Проверяем модель при инициализации
        validate_model(model_name)
        self.config = config
        self.config['model'] = model_name
        
        # Устанавливаем API ключ
        api_keys = config.get('api_keys', [])
        if not api_keys:
            raise ValueError("No API keys provided")
        openai.api_key = api_keys[0]  # Используем первый ключ
        
    async def get_completion(self, messages: List[Dict[str, str]]) -> str:
        # ВАЖНО: Дополнительная проверка перед вызовом API
        validate_model(self.config['model'])
        
        try:
            response = await openai.chat.completions.create(
                model=self.config['model'],  # Используется только gpt-4o-mini
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"Error in OpenAI API call: {str(e)}"
            logging.error(error_msg)
            return error_msg  # Возвращаем текст ошибки как "сырой" ответ

class AzureOpenAIClient:
    def __init__(self, config: Dict[str, Any], model_name: str = 'gpt-4o-mini'):
        # ВАЖНО: Проверяем модель при инициализации
        validate_model(model_name)
        self.config = config
        self.model = model_name
        
        # Azure specific settings
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
        
        # Настройка deployment для конкретных моделей
        self.deployment_mapping = {
            'gpt-4o-mini': os.getenv('AZURE_OPENAI_DEPLOYMENT_4O_MINI', 'gpt-4o-mini')
        }
        
        # Выбираем правильный deployment
        self.deployment = self.deployment_mapping.get(self.model)
        
        # Конфигурация retry и таймауты
        self.max_retries = 3
        self.retry_delay = 1
        self.timeout = 60
        
        # Проверка наличия необходимых параметров
        if not self.endpoint or not self.api_key:
            raise ValueError("Не указаны endpoint или API ключ для Azure OpenAI")
        
        if not self.deployment:
            raise ValueError(f"Не найден deployment для модели {self.model}")
        
        logging.info(f"Инициализирован клиент Azure OpenAI с моделью {self.model}")
        
    def _get_headers(self):
        """Возвращает заголовки для запроса к Azure OpenAI API"""
        return {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }
        
    def _get_api_url(self):
        """Возвращает URL для API запроса к Azure OpenAI"""
        return f"{self.endpoint}openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
        
    async def get_completion(self, messages: List[Dict[str, str]]) -> str:
        # ВАЖНО: Дополнительная проверка перед вызовом API
        validate_model(self.model)
        
        for attempt in range(self.max_retries):
            try:
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
                        if response.status != 200:
                            error_text = await response.text()
                            logging.error(f"Azure API ошибка: {response.status} - {error_text}")
                            if attempt == self.max_retries - 1:
                                return f"Ошибка Azure API: {response.status}"
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                            
                        data = await response.json()
                        return data['choices'][0]['message']['content']
            except Exception as e:
                logging.error(f"Ошибка при вызове Azure API: {str(e)}")
                if attempt == self.max_retries - 1:
                    return f"Ошибка при вызове Azure API: {str(e)}"
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                
        return "Не удалось получить ответ от Azure API после всех попыток"