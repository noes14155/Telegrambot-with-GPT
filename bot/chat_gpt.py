import requests
import openai

class ChatGPT:
    def __init__(self,api_key):
        openai.api_key = api_key
        openai.api_base = "https://chimeragpt.adventblocks.cc/api/v1"
        self.fetch_models_url = 'https://chimeragpt.adventblocks.cc/api/v1/models'
        self.models = []
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        

    def fetch_chat_models(self): 
        response = requests.get(self.fetch_models_url, headers=self.headers)
        if response.status_code == 200:
            ModelsData = response.json()
            for model in ModelsData.get('data'):
                if "chat" in model['endpoints'][0]:
                    self.models.append(model['id'])
        else:
            print(f"Failed to fetch chat models. Status code: {response.status_code}")

        return self.models

    async def generate_response(
        self, instruction, plugin_result, history, prompt, model='gpt-3.5-turbo'
    ):
        text = ''
        messages = [
                {"role": "system", "content": plugin_result},
                {"role": "system", "content": instruction},
                *history,
                {"role": "user", "content": prompt},
            ]
        
        try:
            response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages
                )
            text = response.choices[0].message.content
        except Exception as e:
            text = f'model not available ```{e}```'
            if "rate limit" in text.lower():
                print(f"Rate limit on {model}, retrying with next model")
                model = 'gpt-4' if model == 'gpt-3.5-turbo' else 'gpt-3.5-turbo'
                return await self.generate_response(instruction, plugin_result, history, prompt, model)
        if text == '':
            text = 'Failed to generate a response using the selected model'
        return text
    
   
  