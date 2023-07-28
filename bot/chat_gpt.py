import random
import bot.bing_wrapper as bing
import bot.getgpt_wrapper as ai
import aiohttp
import asyncio
import openai

class ChatGPT:
    def __init__(self,api_key):
        openai.api_key = api_key
        openai.api_base = "https://chimeragpt.adventblocks.cc/api/v1"
        

    async def generate_response(
        self, instruction, plugin_result, history, prompt
    ):
        text = ''
        model = ['gpt-4']
        messages = [
                {"role": "system", "content": plugin_result},
                {"role": "system", "content": instruction},
                *history,
                {"role": "user", "content": prompt},
            ]
        
        for chunk in ai._create_completion(model=model,messages=messages,stream=True):
            text += chunk
      
        return text
    
    async def bing_response(
        self, instruction, plugin_result, history, prompt
    ):
        text = ''
        model = ['gpt-4']
        messages = [
                {"role": "system", "content": plugin_result},
                {"role": "system", "content": instruction},
                *history,
                {"role": "user", "content": prompt},
            ]
        async for chunk in  bing._create_completion(model=model,messages=messages,stream=True):
            text += chunk
        
        return text
    
    async def openai_response(
        self, instruction, plugin_result, history, prompt, model
    ):
        text = ''
        messages = [
                {"role": "system", "content": plugin_result},
                {"role": "system", "content": instruction},
                *history,
                {"role": "user", "content": prompt},
            ]
        response = openai.ChatCompletion.create(
        model=model,
        messages=messages
        )
        text = response.choices[0].message.content
        return text