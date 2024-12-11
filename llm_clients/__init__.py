# llm_clients/__init__.py

from .openai_client import OpenAIClient

def get_llm_client(model_name='gpt-4o', config=None):
    """
    Factory function to get LLM client based on model name
    """
    if not config:
        config = {}
    
    config['model'] = model_name
    
    # В будущем здесь можно добавить другие клиенты
    return OpenAIClient(config)
