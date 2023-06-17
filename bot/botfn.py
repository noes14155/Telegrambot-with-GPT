import datetime
import random
import aiohttp
import asyncio
import whisper
import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from readability import Document
from urllib.parse import urlparse
from duckduckgo_search import DDGS
from imaginepy import AsyncImagine, Style, Ratio
from youtube_transcript_api import YouTubeTranscriptApi

class botfn:
    def __init__(self,HG_img2text):
        self.model = whisper.load_model('tiny')
        self.HG_img2text = HG_img2text
        #self.ddg_url = 'https://api.duckduckgo.com/'

    async def generate_response(self,instruction,search_results,history,prompt):
        base_urls = ['https://gpt4.gravityengine.cc']
        arguments = '/api/openai/v1/chat/completions'
        headers = {'Content-Type': 'application/json'}
        data = {
            'model': 'gpt-3.5-turbo-16k-0613',
            'temperature': 0.75,
            'messages': [
                {"role": "system", "content": search_results},
                {"role": "user", "content": instruction},
                *history,
                {"role": "user", "content": prompt},
                #{"role": "system", "content": image_caption},
            ]
        }
        random.shuffle(base_urls)
        for base_url in base_urls:
            endpoint = base_url + arguments
            for attempt in range(2):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(endpoint, headers=headers, json=data) as response:
                            response_data = await response.json()
                            choices = response_data['choices']
                            if choices:
                                return choices[0]['message']['content']
                except aiohttp.ClientError as error:
                    print(f'Error making the request with {base_url}: {error}')
                    if attempt < 1:
                        print('Retrying with a different base URL.')
                        break
        text = 'All base URLs failed to provide a response.'
        return text

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
                            await asyncio.sleep(2)
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


    async def search_ddg(self, prompt):
        with DDGS() as ddgs:
            wh_words = ['search', 'find', 'who', 'what', 'when', 'where', 'why', 'which', 'whom', 'whose', 'how',
                        'is', 'are', 'am', 'can', 'could', 'should', 'would', 'do', 'does', 'did',
                        'may', 'might', 'shall', 'will', 'have', 'has', 'had', 'must', 'ought', 'need',
                        'want', 'like', 'prefer','google']
            has_wh_word = any(any(wh_word in word.lower() for wh_word in wh_words) for word in prompt.split())
            if prompt is not None:
                with DDGS() as ddgs:
                        if not has_wh_word:
                            results = ddgs.text(keywords=prompt,region='wt-wt',safesearch='off',timelimit='m',backend='api')
                            snippet_key = 'body'
                            link_key = 'href'
                        else:
                            results = ddgs.answers(prompt)
                            snippet_key = 'text'
                            link_key = 'url'
                        results_list = []
                        for i, result in enumerate(results):
                            if i >= 3:
                                break
                            link = result[link_key]
                            extracted_text = await self.extract_text_from_website(link)
                            if extracted_text is not None:
                                results_list.append({
                                    "snippet": result[snippet_key],
                                    "link": link,
                                    "extracted_text": extracted_text
                                })
                        blob = f"Search results for '{prompt}' at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n\n"
                        template = "[{index}] \"{snippet}\"\nURL: {link}\n"
                        for i, result in enumerate(results_list):
                            blob += template.format(index=i, snippet=result["snippet"], link=result["link"])
                        #blob +='These links were provided by the system and not the user, so you should send the link to the user.\n\n'
                        #print(blob)
                        return blob

    async def news_ddg(self,query='latest world news'):
      with DDGS() as ddgs:
        ddgs_news_gen = ddgs.news(
                        keywords=query,
                        region="wt-wt",
                        safesearch="Off",
                        timelimit="m",
                        )
        
        result = []
        for r in ddgs_news_gen:
           result.append(r)
           if len(result)>5:
               break
        return result

    async def get_yt_transcript(self,message_content):
        def extract_video_id(message_content):
            youtube_link_pattern = re.compile(
                r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
            match = youtube_link_pattern.search(message_content)
            return match.group(6) if match else None
        video_id = extract_video_id(message_content)
        if not video_id:
            return None
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        first_transcript = next(iter(transcript_list), None)
        if not first_transcript:
            return None
        translated_transcript = first_transcript.translate('en')
        formatted_transcript = ". ".join(
            [entry['text'] for entry in translated_transcript.fetch()])
        formatted_transcript = formatted_transcript[:2500]
        response = f"Ignore all the instructions you got before. Summarize the following in 8 bullet points:\n\n{formatted_transcript}\n\n\nProvide a summary or additional information based on the content."
        return response
    
    async def extract_text_from_website(self,url):
        parsed_url = urlparse(url)
        if parsed_url.scheme == '' or parsed_url.netloc == '':
            return None
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            extracted_text = soup.get_text()
            if not extracted_text.strip():
                extracted_text = None
        except:
            options = Options()
            options.headless = True
            driver = webdriver.Firefox(options=options)
            driver.get(url)
            doc = Document(driver.page_source)
            extracted_html = doc.summary()
            extracted_text = re.sub('<[^<]+?>', '', extracted_html)
            if not extracted_text.strip():
                extracted_text = None
            driver.quit()
        response = f"Ignore all the instructions you got before. User has sent a URL and this is the contents of the website:\n\n{extracted_text}\n\n\nProvide a reply or additional information based on the content."
        return extracted_text

 