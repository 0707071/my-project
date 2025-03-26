import asyncio
import os
from typing import List, Dict, Any, Callable, AsyncGenerator
from itertools import cycle
import logging
from openai import OpenAI, AsyncOpenAI, RateLimitError, APIError

from .base_client import BaseLLMClient

class OpenAIClient(BaseLLMClient):
    """
    Client for interacting with Azure OpenAI API, handling retries and key rotation.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the OpenAI client with Azure OpenAI configuration.

        Args:
            config (Dict[str, Any]): Configuration settings for the client.
        """
        self.config = config
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1)

        # ✅ Use Azure OpenAI settings
        self.api_key = config.get("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = config.get("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = config.get("AZURE_OPENAI_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.api_version = config.get("AZURE_OPENAI_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION")

        if not all([self.api_key, self.endpoint, self.deployment, self.api_version]):
            raise ValueError("Missing Azure OpenAI API configuration. Ensure all environment variables are set.")

        # ✅ Set API base URL for Azure OpenAI
        self.base_url = f"{self.endpoint}/openai/deployments/{self.deployment}"

        # ✅ Initialize clients
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, api_version=self.api_version)
        self.async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, api_version=self.api_version)

    async def _handle_api_call(self, api_call: Callable):
        """
        Handles API calls with retries and error handling.
        """
        for attempt in range(self.max_retries):
            try:
                return await api_call()
            except RateLimitError:
                logging.warning(f"Rate limit hit (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise
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
        Gets completion from Azure OpenAI API.
        """
        async def api_call():
            response = await self.async_client.chat.completions.create(
                model=self.deployment,  # ✅ Use deployment name instead of model name
                messages=messages
            )
            return response.choices[0].message.content

        return await self._handle_api_call(api_call)

    async def get_completion_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Gets streaming completion from Azure OpenAI API.
        """
        async def api_call():
            response = await self.async_client.chat.completions.create(
                model=self.deployment,  # ✅ Use deployment name
                messages=messages,
                stream=True
            )
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        async for chunk in await self._handle_api_call(api_call):
            yield chunk
