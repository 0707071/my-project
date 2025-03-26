import asyncio
from karhuno.llm_clients.Azure_openai_client import OpenAIClient

async def main():
    # ✅ Define the test configuration
    config = {
        "AZURE_OPENAI_API_KEY": config.get("AZURE_OPENAI_API_KEY"),  # Replace with actual key or use env variable
        "AZURE_OPENAI_ENDPOINT": config.get("AZURE_OPENAI_ENDPOINT"),  # Replace with actual endpoint
        "AZURE_OPENAI_DEPLOYMENT": config.get("AZURE_OPENAI_DEPLOYMENT"),  # Replace with actual deployment name
        "AZURE_OPENAI_API_VERSION": config.get("AZURE_OPENAI_API_VERSION") # Use the correct version
    }

    # ✅ Initialize the OpenAIClient
    client = OpenAIClient(config)

    # ✅ Define a test message
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]

    # ✅ Get a completion from the Azure OpenAI API
    try:
        response = await client.get_completion(messages)
        print("🔹 AI Response:", response)
    except Exception as e:
        print("❌ Error:", e)

# Run the test
asyncio.run(main())
