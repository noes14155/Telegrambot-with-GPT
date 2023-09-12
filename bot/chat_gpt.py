import requests
import openai
from typing import List, Dict, Any, Generator

class ChatGPT:
    def __init__(self,api_key,api_base):
        openai.api_key = api_key
        openai.api_base = api_base

        self.fetch_models_url = f'{api_base}/models'
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

    def generate_response(
        self, instruction: str, plugin_result: str, history: List[Dict[str, str]], prompt: str,
        function: List[Dict[str, Any]] = [], model: str = 'gpt-3.5-turbo'
    ) -> Generator[str, None, None]:
        """
        Generates a response using the selected model and input parameters.
        Args:
            instruction (str): The instruction for generating the response.
            plugin_result (str): The plugin result.
            history (List[Dict[str, str]]): The chat history.
            prompt (str): The user prompt.
            function (List[Dict[str, Any]]): The functions to be used.
            model (str): The selected model.
        Yields:
            str: Each message in the response stream.
        """
        while True:  
            text = ''
            models_index = 0
            if not model.startswith('gpt'):
                plugin_result = ''
                function = []
                print('Unsupported model. Plugins not used')
            messages = [
                {"role": "system", "content": plugin_result},
                {"role": "system", "content": instruction},
                *history,
                {"role": "user", "content": prompt},
            ]
            try:
                response_stream = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    functions=function,
                    stream=True
                )
                return response_stream
            except Exception as e:
                text = f'model not available ```{e}```'
                if "rate limit" in text.lower():
                    print(f"Rate limit on {model}")
                    models_index += 1
                    if models_index >= len(self.models):
                        models_index = 0
                    model = self.models[models_index]
                    print(f"retrying with {model}")
                    continue
                return text