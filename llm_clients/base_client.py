# Path: llm_clients/base_client.py
# This file defines the base abstract class for LLM clients.

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, AsyncGenerator

class BaseLLMClient(ABC):
    """
    Abstract base class for language model clients.
    """

    @abstractmethod
    async def get_completion(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> str:
        """
        Retrieves a completion from the language model.

        Args:
            messages (List[Dict[str, str]]): List of messages to send to the model.
            update_callback (Callable[[], Any], optional): Callback function to update status.

        Returns:
            str: The response from the language model.
        """
        pass

    @abstractmethod
    async def get_completion_stream(self, messages: List[Dict[str, str]], update_callback: Callable[[], Any] = None) -> AsyncGenerator[str, None]:
        """
        Retrieves a streaming completion from the language model.

        Args:
            messages (List[Dict[str, str]]): List of messages to send to the model.
            update_callback (Callable[[], Any], optional): Callback function to update status.

        Yields:
            str: Chunks of the response from the language model.
        """
        pass
