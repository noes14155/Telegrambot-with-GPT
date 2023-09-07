from typing import List, Dict, Any, Generator
import requests
import openai

class ChatGPT:
    def __init__(self, api_key: str, api_base: str):
        """
        Initializes the ChatGPT class with the OpenAI API key and base URL.

        Args:
            api_key (str): The OpenAI API key.
            api_base (str): The OpenAI API base URL.
        """
        openai.api_key = api_key
        openai.api_base = api_base
        self.fetch_models_url = 'https://chimeragpt.adventblocks.cc/api/v1/models'
        self.models = []
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def fetch_chat_models(self) -> List[str]:
        """
        Fetches available chat models from the API and stores their IDs in the `models` field.

        Returns:
            List[str]: A list of available chat model IDs.
        """
        response = requests.get(self.fetch_models_url, headers=self.headers)
        if response.status_code == 200:
            models_data = response.json()
            for model in models_data.get('data'):
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
                for response in response_stream:
                    yield response
            except Exception as e:
                text = f'model not available ```{e}```'
                if "rate limit" in text.lower():
                    print(f"Rate limit on {model}, retrying with another model")
                    model = 'gpt-4' if model == 'gpt-3.5-turbo' else 'gpt-3.5-turbo'
                    continue
                yield text
    
   
  