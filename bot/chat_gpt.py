import time
import requests
import openai
from typing import List, Dict, Any, Generator

class ChatGPT:
    def __init__(self, api_key: str, api_base: str, default_model: str):
        """
        Initializes the ChatGPT instance with the provided API key and base URL.

        Args:
            api_key (str): The OpenAI API key.
            api_base (str): The base URL for the OpenAI API.
        """
        openai.api_key = api_key
        openai.api_base = api_base

        self.fetch_models_url = f'{api_base}/models'
        self.default_model = default_model
        self.models = []
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def fetch_chat_models(self) -> List[str]:
        """
        Fetches available chat models from the OpenAI API and stores them in the models field.

        Returns:
            List[str]: The available chat models.
        """
        
        
        response = requests.get(self.fetch_models_url, headers=self.headers)
        
        if response.status_code == 200:
            models_data = response.json()
            self.models.extend(
                model['id']
                for model in models_data.get('data')
                if "chat" in model['endpoints'][0]
            )
        else:
            print(f"Failed to fetch chat models. Status code: {response.status_code}")
            self.models.append('gpt-4')
            self.models.append('gpt-3.5-turbo')
        if self.default_model not in self.models:
            self.models.append(self.default_model)
        return self.models


    
    def generate_response(self, instruction: str, plugin_result: str, history: List[Dict[str, str]], function: List[Dict[str, Any]] = None, model: str = 'gpt-3.5-turbo') -> Generator[str, None, None]:
        """
        Generates a response using the selected model and input parameters.

        Args:
            instruction (str): The instruction for generating the response.
            plugin_result (str): The plugin result.
            history (List[Dict[str, str]]): The chat history.
            function (List[Dict[str, Any]]): The functions to be used.
            model (str): The selected model.

        Yields:
            str: Each message in the response stream.
        """
        if function is None:
            function = []
        retries = 0
        while True:
            text = ''
            if not model.startswith('gpt'):
                plugin_result = ''
                function = []
                print('Unsupported model. Plugins not used')
            messages = [
                {"role": "system", "content": instruction},
                {"role": "system", "content": plugin_result},
                *history
            ]
            try:
                return openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    functions=function,
                    function_call='auto',
                    stream=True,
                )
            except Exception as e:
                text = f'model not available ```{e}```'
                if "rate limit" in text.lower():
                    retries += 1
                    if retries >= 3:
                        return text
                    print(f"Rate limit on {model}. Retrying after 5 seconds")
                    time.sleep(5)
                    continue
                return text