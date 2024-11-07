import os
import asyncio
import openai
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем ключ API
api_key = os.getenv('OPENAI_API_KEYS', '').split(',')[0]
if not api_key:
    raise ValueError("No OpenAI API key found in environment")

openai.api_key = api_key

async def test_chat_completion():
    """Тестируем Chat Completion API"""
    try:
        print("Testing Chat Completion API...")
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, World!'"}
            ]
        )
        print("Success! Response:", response.choices[0].message.content)
    except Exception as e:
        print(f"Chat Completion Error: {str(e)}")
        print(f"Full error: {repr(e)}")

async def test_completion():
    """Тестируем Completion API"""
    try:
        print("\nTesting Completion API...")
        response = await openai.Completion.acreate(
            model="gpt-4o-mini",
            prompt="Say 'Hello, World!'",
            max_tokens=10
        )
        print("Success! Response:", response.choices[0].text)
    except Exception as e:
        print(f"Completion Error: {str(e)}")
        print(f"Full error: {repr(e)}")

async def main():
    print(f"Using API key: {api_key[:8]}...")
    await test_chat_completion()
    await test_completion()

if __name__ == "__main__":
    asyncio.run(main()) 