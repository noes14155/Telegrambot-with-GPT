import random

import aiohttp

class ChatGPT:
    async def generate_response(
        self, instruction, plugin_name, plugin_result, history, prompt
    ):
        base_urls = ["https://gpt4.xunika.uk/"]
        arguments = "/api/openai/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "gpt-3.5-turbo-16k-0613",
            "temperature": 0.75,
            "messages": [
                {"role": "system", "content": plugin_result},
                {"role": "system", "content": instruction},
                *history,
                {"role": "user", "content": prompt},
            ],
        }
        random.shuffle(base_urls)
        for base_url in base_urls:
            endpoint = base_url + arguments
            for attempt in range(2):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            endpoint, headers=headers, json=data
                        ) as response:
                            response_data = await response.json()
                            choices = response_data.get("choices", [])
                            if choices:
                                return choices[0]["message"]["content"]
                except aiohttp.ClientError as error:
                    print(f"Error making the request with {base_url}: {error}")
                    if attempt < 1:
                        print("Retrying with a different base URL.")
                        break
        text = "All base URLs failed to provide a response."
        return text