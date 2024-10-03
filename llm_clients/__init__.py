# llm_clients/__init__.py

from .openai_client import OpenAIClient

def get_llm_client(provider, config):
    if provider.lower() == 'openai':
        return OpenAIClient(config)
    else:
        raise ValueError(f"Провайдер {provider} не поддерживается.")
