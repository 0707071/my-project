# Файл: llm_clients/cohere_client.py

import asyncio
import os
from typing import List, Dict, Any, Callable, AsyncGenerator, Optional
from .base_client import BaseLLMClient
import cohere
from itertools import cycle
import logging

logger = logging.getLogger(__name__)

class CohereClient(BaseLLMClient):
    """
    Клиент для работы с Cohere API с балансировкой ключей.
    """

    def __init__(self, config):
        self.config = config
        self.api_keys = self._load_api_keys()
        self.current_key = next(self.api_keys)
        self.model = config.get('COHERE_MODEL', 'default-model')
        self.max_retries = config.get('MAX_RETRIES', 3)
        self.retry_delay = config.get('RETRY_DELAY', 1)  # В секундах

    def _load_api_keys(self):
        """
        Загружает ключи API из переменной окружения COHERE_API_KEYS.
        """
        keys = os.getenv("COHERE_API_KEYS", "").split(",")
        keys = [key.strip() for key in keys if key.strip()]
        if not keys:
            raise ValueError("Не найдены ключи API для Cohere в переменных окружения.")
        return cycle(keys)

    def _get_client(self):
        return cohere.Client(api_key=self.current_key)

    async def _handle_api_call(self, api_call: Callable):
        """
        Обрабатывает вызов API с учетом повторных попыток и смены ключей.
        """
        for attempt in range(self.max_retries):
            try:
                return await api_call()
            except Exception as e:
                logger.error(f"Cohere API error: {str(e)}")
                if "rate limit" in str(e).lower():
                    self.current_key = next(self.api_keys)
                    logger.info(f"Переключение на следующий API-ключ: {self.current_key[:5]}...")
                elif attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def get_completion(self, messages: List[Dict[str, str]], update_callback: Optional[Callable[[], Any]] = None) -> str:
        async def api_call():
            client = self._get_client()
            # Форматирование сообщений для Cohere
            formatted_messages = self._format_messages(messages)
            logger.debug(f"Отправка запроса в Cohere API: {formatted_messages}")

            # Предполагается, что Cohere использует prompt, объединяя все сообщения
            prompt = "\n".join([msg['content'] for msg in formatted_messages])
            response = await asyncio.to_thread(
                client.generate,
                prompt=prompt,
                model=self.model,
                max_tokens=self.config.get('MAX_TOKENS', 2000),
                temperature=self.config.get('TEMPERATURE', 0.6),
            )
            logger.debug(f"Получен ответ от Cohere API: {response.generations[0].text}")
            return response.generations[0].text.strip()

        return await self._handle_api_call(api_call)

    async def get_completion_stream(self, messages: List[Dict[str, str]], update_callback: Optional[Callable[[], Any]] = None) -> AsyncGenerator[str, None]:
        """
        Cohere не поддерживает стриминг ответов, поэтому возвращаем полный ответ.
        """
        completion = await self.get_completion(messages, update_callback)
        yield completion

    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Форматирует сообщения в формат, ожидаемый API Cohere.
        """
        return [{"role": msg["role"].upper(), "content": msg["content"]} for msg in messages]
