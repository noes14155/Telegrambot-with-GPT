import aiohttp
import asyncio
import os
import whisper
import pypdf
from imaginepy import AsyncImagine, Style, Ratio

class botmedia:
    def __init__(self,HG_img2text):
        self.model = whisper.load_model('tiny')
        self.HG_img2text = HG_img2text
    async def generate_imagecaption(self, url, HG_TOKEN):
        headers = {"Authorization": f"Bearer {HG_TOKEN}"}
        max_retries = 3
        retries = 0
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp1, session.post(self.HG_img2text, headers=headers, data=await resp1.read()) as resp2:
                    response = await resp2.json()
                    if resp2.status == 200:
                        return f"This image looks like a" + response[0]['generated_text']
                    elif resp2.status >= 500 or 'loading' in response.get('error', '').lower():
                        retries += 1
                        if retries <= max_retries:
                            await asyncio.sleep(3)
                        else:
                            return f"Server error: {await resp2.content.read()}"
                    else:
                        return f"Error: {response.get('error')}"

    async def generate_image(self,image_prompt, style_value, ratio_value, negative):
        imagine = AsyncImagine()
        filename = "image.png"
        style_enum = Style[style_value]
        ratio_enum = Ratio[ratio_value]
        img_data = await imagine.sdprem(
            prompt=image_prompt,
            style=style_enum,
            ratio=ratio_enum,
            priority="1",
            high_res_results="1",
            steps="70",
            negative=negative
        )
        try:
            with open(filename, mode="wb") as img_file:
                img_file.write(img_data)
        except Exception as e:
            print(f"An error occurred while writing the image to file: {e}")
            return None
        await imagine.close()
        return filename
    
    async def transcribe_audio(self, audio_file_path):
        with open(audio_file_path, 'rb') as audio_file:
            content = audio_file.read()

        result = self.model.transcribe(audio_file_path)
        transcription = result["text"]
        return transcription
    
    async def download_file_from_message(self,bot,message):
        if message.audio is not None:
            file = message.audio
            file_extension = file.file_name.split(".")[-1] if file.file_name is not None else '.ogg'
        elif message.voice is not None:
            file = message.voice
            file_extension = file.file_name.split(".")[-1] if file.file_name is not None else '.ogg'
        elif message.document is not None:
            file = message.document
            file_extension = file.file_name.split(".")[-1] if file.file_name is not None else ''
        else:
            return None
        file_path = f'{file.file_id}.{file_extension}'
        file_dir = 'downloaded_files'
        os.makedirs(file_dir, exist_ok=True)
        full_file_path = os.path.join(file_dir, file_path)
        file_info = await bot.get_file(file.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        with open(full_file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        return full_file_path
    
    async def read_document(self,filename):
        valid_extensions = ['txt', 'rtf', 'md', 'html', 'xml', 'csv', 'json', 'js', 'css', 'py', 'java', 'c', 'cpp', 'php', 'rb', 'swift', 'sql', 'sh', 'bat', 'ps1', 'ini', 'cfg', 'conf', 'log', 'svg', 'epub', 'mobi', 'tex', 'docx', 'odt', 'xlsx', 'ods', 'pptx', 'odp', 'eml', 'htaccess', 'nginx.conf', 'pdf']
        extension = filename.split('.')[-1]
        if extension not in valid_extensions:
            return 'Invalid document file'
        if extension == 'pdf':
            with open(filename, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                contents = ''
                for page_num in range(num_pages):
                    page_obj = pdf_reader.pages[page_num]
                    page_text = page_obj.extract_text()
                    contents += page_text
            return contents
        else:
            with open(filename, 'r') as f:
                contents = f.read()
                return contents