import random
import bot.bing_wrapper as ai
import bot.getgpt_wrapper as ai
import aiohttp
import asyncio

class ChatGPT:
    async def generate_response(
        self, instruction, plugin_name, plugin_result, history, prompt
    ):
        text = ''
        model = ['gpt-4']
        messages = [
                {"role": "system", "content": plugin_result},
                {"role": "system", "content": instruction},
                *history,
                {"role": "user", "content": prompt},
            ]
        #async for chunk in  ai._create_completion(model=model,messages=messages,stream=True):
        #    text += chunk
        for chunk in ai._create_completion(model=model,messages=messages,stream=True):
            text += chunk
      
        return text