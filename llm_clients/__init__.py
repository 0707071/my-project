# llm_clients/__init__.py
# ВАЖНО: В проекте используется только модель gpt-4o-mini
# Не заменять на gpt-4, gpt-4-turbo или другие модели без явного разрешения техлида
# Это критично для контроля расходов

import os
import logging
from typing import Dict, Any, Optional
from .openai_client import OpenAIClient
from .azure_client import AzureOpenAIClient

# Отключаем SDK клиент, так как не удалось установить библиотеку
AZURE_SDK_AVAILABLE = False
logging.warning("SDK Azure OpenAI отключен. Используем обычный HTTP API клиент.")

def get_llm_client(model_name: str = 'gpt-4o-mini', config: Optional[Dict[str, Any]] = None, provider: str = 'azure') -> AzureOpenAIClient:
    """
    Factory function to get LLM client based on model name and provider
    ВАЖНО: Единственная разрешенная модель - gpt-4o-mini
    
    Args:
        model_name (str): Название модели, должно быть только 'gpt-4o-mini'
        config (Optional[Dict[str, Any]]): Конфигурация клиента
        provider (str): Провайдер API ('azure', 'azure_sdk' или 'openai'), по умолчанию 'azure'
    
    Returns:
        BaseLLMClient: Клиент для выбранного провайдера
    """
    if not config:
        config = {}
    
    # ВАЖНО: Модель всегда должна быть gpt-4o-mini
    if model_name != 'gpt-4o-mini':
        raise ValueError(f"Модель {model_name} не разрешена. Используйте только gpt-4o-mini")
    
    config['model'] = model_name
    
    # Выбираем клиента в зависимости от провайдера
    if provider.lower() == 'openai':
        return OpenAIClient(config)  # OpenAIClient содержит дополнительные проверки модели
    elif provider.lower() == 'azure_sdk':
        logging.warning("SDK Azure OpenAI недоступен, используем обычный HTTP клиент Azure")
        return AzureOpenAIClient(config)  # SDK клиент не используем, так как его нельзя установить
    elif provider.lower() == 'azure':
        return AzureOpenAIClient(config)  # По умолчанию используем Azure
    else:
        raise ValueError(f"Неизвестный провайдер: {provider}. Доступны: 'azure', 'azure_sdk', 'openai'")
