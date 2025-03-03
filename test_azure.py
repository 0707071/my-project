#!/usr/bin/env python3
import os
import asyncio
import logging
from llm_clients import get_llm_client

logging.basicConfig(level=logging.INFO)

async def test_azure_client():
    print("Создаю клиент Azure OpenAI...")
    client = get_llm_client()
    print(f"Тип клиента: {type(client)}")
    
    try:
        print("Отправляю запрос к Azure OpenAI...")
        messages = [
            {"role": "user", "content": "Hello! Tell me what model you are using?"}
        ]
        
        result = await client.get_completion(messages)
        print("\nОтвет от Azure OpenAI:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
        print("\nКлиент Azure успешно работает!")
    except Exception as e:
        print(f"\nОшибка при вызове Azure API: {str(e)}")
        
        # Проверяем, что переменные окружения заданы
        print("\nПроверка переменных окружения:")
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_4O_MINI')
        
        print(f"AZURE_OPENAI_ENDPOINT: {'Задан' if endpoint else 'НЕ ЗАДАН'}")
        print(f"AZURE_OPENAI_API_KEY: {'Задан' if api_key else 'НЕ ЗАДАН'}")
        print(f"AZURE_OPENAI_DEPLOYMENT_4O_MINI: {'Задан' if deployment else 'НЕ ЗАДАН'}")

if __name__ == "__main__":
    asyncio.run(test_azure_client()) 