# llm_clients/__init__.py
# ВАЖНО: В проекте используется только модель gpt-4o-mini
# Не заменять на gpt-4, gpt-4-turbo или другие модели без явного разрешения техлида
# Это критично для контроля расходов

from typing import Dict, Any, Optional
from .openai_client import OpenAIClient

def get_llm_client(model_name: str = 'gpt-4o-mini', config: Optional[Dict[str, Any]] = None) -> OpenAIClient:
    """
    Factory function to get LLM client based on model name
    ВАЖНО: Единственная разрешенная модель - gpt-4o-mini
    """
    if not config:
        config = {}
    
    # ВАЖНО: Модель всегда должна быть gpt-4o-mini
    config['model'] = model_name
    
    return OpenAIClient(config)  # OpenAIClient содержит дополнительные проверки модели
