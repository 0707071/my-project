from typing import Dict, List, AsyncGenerator, Any

class BaseLLMClient:
    """Базовый класс для LLM клиентов"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
    async def get_completion(self, messages: List[Dict[str, str]]) -> str:
        """Получает завершение от модели"""
        raise NotImplementedError
        
    async def get_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Получает потоковый ответ от модели"""
        raise NotImplementedError 