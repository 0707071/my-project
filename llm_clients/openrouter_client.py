# quantum_rpg_bot/llm_clients/openrouter_client.py

import asyncio
from typing import List, Dict, Any, Callable, AsyncGenerator
from config import Config
from .base_client import BaseLLMClient
from openai import AsyncOpenAI
from itertools import cycle

class OpenRouterClient(BaseLLMClient):
    """
    Клиент для работы с OpenRouter API, используя синтаксис, совместимый с OpenAI.
    """

    def __init__(self, config: Config):
        self.api_keys = cycle(config.OPENROUTER_API_KEYS)
        self.model = config.OPENROUTER_MODEL
        self.max_retries = config.MAX_RETRIES
        self.retry_delay = config.RETRY_DELAY
        self.timeout = config.GPT_TIMEOUT
        self.max_tokens = config.MAX_TOKENS
        self.temperature = config.TEMPERATURE
        self.top_p = config.TOP_P
        self.top_k = config.TOP_K
        self.repetition_penalty = config.REPETITION_PENALTY

    def _get_client(self):
        return AsyncOpenAI(
            api_key=next(self.api_keys),
            base_url="https://openrouter.ai/api/v1"
        )

    async def get_completion(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> str:
        for attempt in range(self.max_retries):
            try:
                client = self._get_client()
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        top_p=self.top_p,
                    ),
                    timeout=self.timeout
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                if update_callback:
                    await update_callback()
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def get_completion_stream(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> AsyncGenerator[str, None]:
        for attempt in range(self.max_retries):
            try:
                client = self._get_client()
                stream = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    stream=True
                )
                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                if update_callback:
                    await update_callback()
                await asyncio.sleep(self.retry_delay * (attempt + 1))