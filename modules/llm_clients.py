import openai
from typing import Dict, Any, List

# ВАЖНО: В проекте используется только модель gpt-4o-mini
# Не заменять на gpt-4, gpt-4-turbo или другие модели без явного разрешения техлида
# Это критично для контроля расходов

class ModelError(Exception):
    """Исключение при попытке использовать неразрешенную модель"""
    pass

def validate_model(model: str) -> None:
    """
    Проверяет, что используется разрешенная модель.
    ВАЖНО: Единственная разрешенная модель - gpt-4o-mini
    """
    ALLOWED_MODEL = 'gpt-4o-mini'
    if model != ALLOWED_MODEL:
        raise ModelError(
            f"Попытка использовать неразрешенную модель: {model}. "
            f"Разрешена только модель {ALLOWED_MODEL}. "
            "Использование других моделей запрещено для контроля расходов."
        )

def get_llm_client(model_name: str, config: Dict[str, Any]) -> 'OpenAIClient':
    # ВАЖНО: Проверяем модель при создании клиента
    validate_model(model_name)
    return OpenAIClient(config, model_name)

class OpenAIClient:
    def __init__(self, config: Dict[str, Any], model_name: str = 'gpt-4o-mini'):
        # ВАЖНО: Проверяем модель при инициализации
        validate_model(model_name)
        self.config = config
        self.config['model'] = model_name
        
    async def get_completion(self, messages: List[Dict[str, str]]) -> str:
        # ВАЖНО: Дополнительная проверка перед вызовом API
        validate_model(self.config['model'])
        
        response = await openai.chat.completions.create(
            model=self.config['model'],  # Используется только gpt-4o-mini
            messages=messages
        )
        return response.choices[0].message.content