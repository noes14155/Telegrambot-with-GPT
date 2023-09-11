import asyncio
import aiohttp
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
import gradio as gr
from gradio_client import Client
import threading
import  openai
import io

class ImageGenerator:
    def __init__(self, HG_IMG2TEXT):
        self.HG_IMG2TEXT = HG_IMG2TEXT
        def load_gradio():
            gr.load("models/stabilityai/stable-diffusion-2-1").launch(server_port=7860)

        gradio_thread = threading.Thread(target=load_gradio)
        gradio_thread.start()
        
    
    async def generate_imagecaption(self, url, HG_TOKEN):
        headers = {"Authorization": f"Bearer {HG_TOKEN}"}
        retries = 0
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp1:
                if resp1.status != 200:
                    return f"Error: failed to download image ({resp1.status})"
                async with session.post(
                    self.HG_IMG2TEXT, headers=headers, data=await resp1.read()
                ) as resp2:
                    if resp2.status == 200:
                        response = await resp2.json()
                        return (
                            "This image looks like a " + response[0]["generated_text"]
                        )
                    elif (
                        resp2.status >= 500 or "loading" in (await resp2.text()).lower()
                    ):
                        retries += 1
                        if retries <= 3:
                            await asyncio.sleep(3)
                            return await self.generate_imagecaption(url, HG_TOKEN)
                        else:
                            return f"Server error: {await resp2.text()}"
                    else:
                        return f"Error: {await resp2.text()}"

    async def generate_image(prompt):
        client = Client("http://127.0.0.1:7860/")
        text = client.predict(prompt, api_name="/predict" )
        return text
    
    async def dalle_generate(self, prompt, size):
        response = openai.Image.create(
            prompt=prompt,
            size=size
        )
        image_url = response["data"][0]["url"]
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                content = await response.content.read()
                img_file = io.BytesIO(content)
                return img_file