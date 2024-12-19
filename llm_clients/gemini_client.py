# quantum_rpg_bot/llm_clients/gemini_client.py

import asyncio
import google.generativeai as genai
from typing import List, Dict, Any, Callable
# from config import Config
from .base_client import BaseLLMClient
from itertools import cycle

class GeminiClient(BaseLLMClient):
    """
    Клиент для работы с Gemini Pro с поддержкой нескольких API ключей.
    Обеспечивает балансировку нагрузки и обратную совместимость с существующим кодом.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initializes the Gemini client with API keys and configuration settings.

        Args:
            config (Dict[str, Any], optional): Configuration settings. Defaults to None.
        """
        # Load API keys from environment variable
        api_keys_env = os.getenv('GEMINI_API_KEYS')
        if not api_keys_env:
            raise ValueError("GEMINI_API_KEYS environment variable is not set")
        
        # Expect keys to be comma-separated
        self.api_keys = [key.strip() for key in api_keys_env.split(',') if key.strip()]
        if not self.api_keys:
            raise ValueError("No valid Gemini API keys found")
        
        self.key_cycle = cycle(self.api_keys)

        # Load configuration from environment variables
        self.max_retries = int(os.getenv('GEMINI_MAX_RETRIES', 5))  # Default 5 retries
        self.retry_delay = int(os.getenv('GEMINI_RETRY_DELAY', 1))  # Default 1 second between retries
        self.timeout = int(os.getenv('GEMINI_TIMEOUT', 60))  # Default 60 seconds timeout

    def _get_model(self):
        """
        Creates and returns a new Gemini Pro model with the next API key from the cycle.

        Returns:
            GenerativeModel: Configured generative model for Gemini Pro.
        """
        key = next(self.key_cycle)
        print(f"Using API key: {key}")
        genai.configure(api_key=key)
        return genai.GenerativeModel('gemini-pro')

    @property
    def model(self):
        """
        Property to maintain backward compatibility.
        Returns a new model upon each access.

        Returns:
            GenerativeModel: Configured generative model for Gemini Pro.
        """
        return self._get_model()

    async def get_completion(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> str:
        """
        Sends a request to the Gemini Pro API to get a completion for the given messages.

        Args:
            messages (List[Dict[str, str]]): The list of messages for the LLM.
            update_callback (Callable[[], Any], optional): Callback function to update status.

        Returns:
            str: The completion result from the API.
        """
        prompt = self._format_messages(messages)
        for attempt in range(self.max_retries):
            try:
                model = self._get_model()
                response = await asyncio.wait_for(
                    model.generate_content_async(prompt),
                    timeout=self.timeout
                )
                return response.text
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                if update_callback:
                    await update_callback()
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def get_completion_stream(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None):
        """
        Sends a request to the Gemini Pro API to get a streaming completion for the given messages.

        Args:
            messages (List[Dict[str, str]]): The list of messages for the LLM.
            update_callback (Callable[[], Any], optional): Callback function to update status.

        Yields:
            str: Chunks of the completion response from the API.
        """
        prompt = self._format_messages(messages)
        for attempt in range(self.max_retries):
            try:
                model = self._get_model()
                response = await model.generate_content_async(prompt, stream=True)
                async for chunk in response:
                    yield chunk.text
                return
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                if update_callback:
                    await update_callback()
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Formats messages into a string suitable for Gemini Pro.

        Args:
            messages (List[Dict[str, str]]): List of messages with roles and content.

        Returns:
            str: Formatted string for Gemini Pro.
        """
        formatted_messages = []
        for message in messages:
            role = message['role']
            content = message['content']
            formatted_messages.append(f"{role.capitalize()}: {content}")
        return "\n".join(formatted_messages)