import openai

def get_llm_client(model_name, config):
    return OpenAIClient(config, model_name)

class OpenAIClient:
    def __init__(self, config, model_name='gpt-4o'):
        self.config = config
        self.model_name = model_name

    async def get_completion(self, messages):
        response = await openai.chat.completions.create(
            model=self.model_name,
            messages=messages
        )
        return response.choices[0].message.content