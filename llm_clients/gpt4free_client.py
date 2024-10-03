import g4f
import asyncio
import logging
from typing import List, Dict, Any, AsyncGenerator, Callable
from config import Config
from .base_client import BaseLLMClient

class GPT4FreeClient(BaseLLMClient):
    """
    Клиент для работы с GPT4Free.
    """

    def __init__(self, config: Config):
        self.logger = logging.getLogger(__name__)
        self.provider = getattr(g4f.Provider, config.GPT4FREE_PROVIDER)
        self.model = config.GPT4FREE_MODEL
        self.max_retries = config.MAX_RETRIES
        self.retry_delay = config.RETRY_DELAY
        self.timeout = config.GPT_TIMEOUT

    async def get_completion(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> str:
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.wait_for(
                    g4f.ChatCompletion.create_async(
                        model=self.model,
                        messages=messages,
                        provider=self.provider,
                    ),
                    timeout=self.timeout
                )
                result = ''.join(response)  # Объединяем все части ответа в одну строку
                if update_callback:
                    update_callback()
                return result
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def get_completion_stream(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> AsyncGenerator[str, None]:
        for attempt in range(self.max_retries):
            self.logger.info("Начало получения потокового ответа от языковой модели")
            try:
                response = await g4f.ChatCompletion.create_async(
                    model=self.model,
                    messages=messages,
                    provider=self.provider,
                )
                for chunk in response:
                    self.logger.debug(f"Получен чанк от модели: {chunk[:50]}...")
                    yield chunk
                    if update_callback:
                        update_callback()
                return
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))