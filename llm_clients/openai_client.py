# Path: llm_clients/openai_client.py
# This file defines the client for interacting with the OpenAI API, handling key rotation and rate limit errors.

import asyncio
import os
from typing import List, Dict, Any, Callable, AsyncGenerator
from itertools import cycle
import logging
from openai import OpenAI, AsyncOpenAI, RateLimitError, APIError

from .base_client import BaseLLMClient

class OpenAIClient(BaseLLMClient):
    """
    Client for interacting with the OpenAI API, including key balancing and exhausted key handling.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the OpenAI client with configuration settings.

        Args:
            config (Dict[str, Any]): Configuration settings for the client.
        """
        self.config = config
        self.model = config.get('model', 'gpt-4o-mini')
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1)
        
        # Инициализация API ключей
        self.api_keys = config.get('api_keys', [os.getenv('OPENAI_API_KEY')])
        if not self.api_keys or not any(self.api_keys):
            raise ValueError("No OpenAI API keys provided")
        
        # Удаляем пустые ключи и создаем цикл
        self.api_keys_list = [k for k in self.api_keys if k and k.strip()]
        self.api_keys_cycle = cycle(self.api_keys_list)
        self.current_key = next(self.api_keys_cycle)
        
        # Создаем синхронный и асинхронный клиенты
        self.client = OpenAI(api_key=self.current_key)
        self.async_client = AsyncOpenAI(api_key=self.current_key)

    def _rotate_key(self):
        """Rotates to the next API key"""
        self.current_key = next(self.api_keys_cycle)
        self.client = OpenAI(api_key=self.current_key)
        self.async_client = AsyncOpenAI(api_key=self.current_key)
        logging.info("Rotated to next API key")

    async def _handle_api_call(self, api_call: Callable):
        """
        Handles API calls with retries and key rotation.
        """
        for attempt in range(self.max_retries):
            try:
                return await api_call()
            except RateLimitError:
                logging.warning(f"Rate limit hit (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise
                self._rotate_key()
            except APIError as e:
                logging.error(f"API error (attempt {attempt + 1}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                logging.error(f"Unexpected error (attempt {attempt + 1}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def get_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Gets completion from OpenAI API.
        """
        async def api_call():
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content

        return await self._handle_api_call(api_call)

    async def get_completion_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Gets streaming completion from OpenAI API.
        """
        async def api_call():
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        async for chunk in await self._handle_api_call(api_call):
            yield chunk
