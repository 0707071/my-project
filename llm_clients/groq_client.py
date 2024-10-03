# quantum_rpg_bot/llm_clients/groq_client.py

import asyncio
from typing import List, Dict, Any, Callable, AsyncGenerator
from config import Config
from .base_client import BaseLLMClient
from groq import AsyncGroq

class GroqClient(BaseLLMClient):
    """
    Клиент для работы с GROQ API.
    """

    def __init__(self, config: Config):
        self.api_key = config.GROQ_API_KEY
        self.model = config.GROQ_MODEL
        self.max_retries = config.MAX_RETRIES
        self.retry_delay = config.RETRY_DELAY
        self.timeout = config.GPT_TIMEOUT
        self.client = AsyncGroq(api_key=self.api_key)

    async def get_completion(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> str:
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.7
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
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7,
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