import asyncio
import aiohttp
import gradio as gr
from gradio_client import Client
import threading
import  openai

class ImageGenerator:
    """
    The `ImageGenerator` class is responsible for generating image captions and images using various AI models.
    It uses the `gradio` library to launch a server for image caption generation and the `openai` library to generate images.
    """

    def __init__(self, HG_IMG2TEXT: str, HG_TEXT2IMAGE: str):
        """
        Initializes the `ImageGenerator` class and launches the `gradio` server in a separate thread.

        Args:
            HG_IMG2TEXT (str): The API endpoint for image-to-text conversion.
        """
        self.HG_IMG2TEXT = HG_IMG2TEXT
        self.HG_TEXT2IMAGE = HG_TEXT2IMAGE
        gradio_thread = threading.Thread(target=self.load_gradio)
        gradio_thread.start()

    def load_gradio(self):
        gr.load(f"models/{self.HG_TEXT2IMAGE}").launch(server_port=7860)

    async def generate_imagecaption(self, url: str, HG_TOKEN: str) -> str:
        """
        Generates a caption for the given image URL by sending a request to the `HG_IMG2TEXT` API endpoint.
        Retries the request if there is a server error or the response is still loading.

        Args:
            url (str): The URL of the image.
            HG_TOKEN (str): The token for authorization.

        Returns:
            str: The generated caption for the image.
        """
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

    async def generate_image(self, prompt: str) -> str:
        """
        Generates an image using the `openai` library by providing a prompt.

        Args:
            prompt (str): The prompt for generating the image.

        Returns:
            str: The generated image as text.
        """
        client = Client("http://127.0.0.1:7860/")
        return client.predict(prompt, api_name="/predict")
        

    async def dalle_generate(self, prompt: str, size: int) -> str:
        """
        Generates an image using the `openai` library by providing a prompt and size.

        Args:
            prompt (str): The prompt for generating the image.
            size (int): The size of the image.

        Returns:
            str: The URL of the generated image.
        """
        try:
            response = openai.Image.create(
                prompt=prompt,
                size=size
            )
            image_url = response["data"][0]["url"]
        except Exception as e:
            return str(e)
        return image_url