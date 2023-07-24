import os
import json
import random
import hashlib
import requests

url = 'https://deepai.org'
model = ['gpt-3.5-turbo']
supports_stream = True
needs_auth = False
working = True


def _create_completion(model: str, messages: list, stream: bool, **kwargs):
    def md5(text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[::-1]


    def get_api_key(user_agent: str) -> str:
        part1 = str(random.randint(0, 10**11))
        part2 = md5(user_agent + md5(user_agent + md5(user_agent + part1 + "x")))
        
        return f"tryit-{part1}-{part2}"

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

    headers = {
        "api-key": get_api_key(user_agent),
        "user-agent": user_agent
    }

    files = {
        "chat_style": (None, "chat"),
        "chatHistory": (None, json.dumps(messages))
    }

    r = requests.post("https://api.deepai.org/chat_response", headers=headers, files=files, stream=True)

    for chunk in r.iter_content(chunk_size=None):
        r.raise_for_status()
        yield chunk.decode()


