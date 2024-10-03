# Path: llm_clients/openai_client.py
# This file defines the client for interacting with the OpenAI API, handling key rotation and rate limit errors.

import asyncio
import os
from typing import List, Dict, Any, Callable, AsyncGenerator
from itertools import cycle
import logging
import openai

from .base_client import BaseLLMClient

class OpenAIClient(BaseLLMClient):
    """
    Client for interacting with the OpenAI API, including key balancing and exhausted key handling.
    """

    EXHAUSTED_MARKER = "#EXHAUSTED#"

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the OpenAI client with configuration settings.

        Args:
            config (Dict[str, Any]): Configuration settings for the client.
        """
        self.model = config.get('model', 'gpt-4o-mini')  # Default to gpt-4o-mini
        self.max_retries = config.get('max_retries', 5)
        self.retry_delay = config.get('retry_delay', 1)  # in seconds
        self.timeout = config.get('timeout', 60)  # in seconds
        self.max_tokens = config.get('max_tokens', 1500)
        self.temperature = config.get('temperature', 0.7)
        self.top_p = config.get('top_p', 0.9)
        self.rate_limit = config.get('rate_limit', 20)  # Requests per minute
        self.rate_limit_period = config.get('rate_limit_period', 60)  # Period in seconds

        # Setting API keys from environment variables
        self.api_keys_env = os.getenv('OPENAI_API_KEYS')
        if not self.api_keys_env:
            raise ValueError("The OPENAI_API_KEYS environment variable is not set.")

        # Expect keys to be comma-separated
        self.api_keys_list = [key.strip() for key in self.api_keys_env.split(',') if key.strip()]
        if not self.api_keys_list:
            raise ValueError("The OPENAI_API_KEYS environment variable does not contain any valid keys.")

        self.api_keys = cycle(self.api_keys_list)
        self.current_key = next(self.api_keys)

        openai.api_key = self.current_key

    def _mark_key_as_exhausted(self, key: str):
        """
        Marks the given API key as exhausted and rotates to the next key.

        Args:
            key (str): The exhausted API key.
        """
        logging.warning(f"Key marked as exhausted: {key}")
        self.api_keys_list = [k for k in self.api_keys_list if k != key]
        if not self.api_keys_list:
            raise ValueError("All API keys are exhausted.")
        self.api_keys = cycle(self.api_keys_list)
        self.current_key = next(self.api_keys)
        openai.api_key = self.current_key

    async def _handle_api_call(self, api_call: Callable):
        """
        Handles API calls with retries in case of rate limit or other API errors.

        Args:
            api_call (Callable): The API call function to execute.

        Returns:
            Any: The result of the API call.
        """
        for attempt in range(self.max_retries):
            try:
                return await api_call()
            except openai.error.RateLimitError as e:
                logging.error(f"Rate limit error: {e}. Switching to the next key.")
                self._mark_key_as_exhausted(self.current_key)
                self.current_key = next(self.api_keys)
                openai.api_key = self.current_key
            except openai.error.APIError as e:
                logging.error(f"API error: {e}")
                if attempt == self.max_retries - 1:
                    raise
                logging.info(f"Retrying in {self.retry_delay} seconds (attempt {attempt + 1})...")
                await asyncio.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                logging.error(f"General error: {e}")
                if attempt == self.max_retries - 1:
                    raise
                logging.info(f"Retrying in {self.retry_delay} seconds (attempt {attempt + 1})...")
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def get_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Sends a request to the OpenAI API to get a completion for the given messages.

        Args:
            messages (List[Dict[str, str]]): The list of messages for the LLM.

        Returns:
            str: The completion result from the API.
        """
        async def api_call():
            # Use asyncio.to_thread to run the synchronous OpenAI API call in an async function
            return await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p
            )

        response = await self._handle_api_call(api_call)
        return response.choices[0].message['content']

    async def get_completion_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Sends a request to the OpenAI API to get a streaming completion for the given messages.

        Args:
            messages (List[Dict[str, str]]): The list of messages for the LLM.

        Yields:
            str: Chunks of the completion response from the API.
        """
        async def api_call():
            return await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                stream=True
            )

        async for chunk in await self._handle_api_call(api_call):
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
