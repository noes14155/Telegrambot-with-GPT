import datetime
import random
import aiohttp
import re
import requests
from aiogram.types import  ReplyKeyboardMarkup, KeyboardButton
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from readability import Document
from urllib.parse import urlparse
from duckduckgo_search import DDGS
from youtube_transcript_api import YouTubeTranscriptApi
import yaml

class botfn:
    def __init__(self,lang):
        self.lang = lang
        self._STYLE_OPTIONS = {
	                        'Imagine V3':'IMAGINE_V3',
                            'Imagine V4 Beta':'IMAGINE_V4_Beta',
                            'Imagine V4 creative':'V4_CREATIVE',
                            'Anime':'ANIME_V2',
                            'Realistic':'REALISTIC',
                            'Disney':'DISNEY',
                            'Studio Ghibli':'STUDIO_GHIBLI',
                            'Graffiti':'GRAFFITI',
                            'Medieval':'MEDIEVAL',
                            'Fantasy':'FANTASY',
                            'Neon':'NEON',
                            'Cyberpunk':'CYBERPUNK',
                            'Landscape':'LANDSCAPE',
                            'Japanese Art':'JAPANESE_ART',
                            'Steampunk':'STEAMPUNK',
                            'Sketch':'SKETCH',
                            'Comic Book':'COMIC_BOOK',
                            'Cosmic':'COMIC_V2',
                            'Logo':'LOGO',
                            'Pixel art':'PIXEL_ART',
                            'Interior':'INTERIOR',
                            'Mystical':'MYSTICAL',
                            'Super realism':'SURREALISM',
                            'Minecraft':'MINECRAFT',
                            'Dystopian':'DYSTOPIAN'
                            }
        self._RATIO_OPTIONS = {'1x1':'RATIO_1X1',
                        '9x16':'RATIO_9X16',
                        '16x9':'RATIO_16X9',
                        '4x3':'RATIO_4X3',
                        '3x2':'RATIO_3X2'}

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
                {"role": "system", "content": instruction},
                *history,
                {"role": "user", "content": prompt},
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
                            choices = response_data.get('choices', [])
                            if choices:
                                return choices[0]['message']['content']
                except aiohttp.ClientError as error:
                    print(f'Error making the request with {base_url}: {error}')
                    if attempt < 1:
                        print('Retrying with a different base URL.')
                        break
        text = 'All base URLs failed to provide a response.'
        return text

    async def search_ddg(self, prompt):
        with DDGS() as ddgs:
            if re.search(r'(https?://\S+)', prompt) or len(prompt) > 1000:
                return
            if prompt is not None:
                    results = ddgs.text(keywords=prompt,region='wt-wt',safesearch='off',backend='api')
                    results_list = []
                    for i, result in enumerate(results):
                        if i >= 3:
                            break
                        #extracted_text = await self.extract_text_from_website(result.get('href'))
                        #if extracted_text is not None:
                        results_list.append({
                            "snippet": result.get('body'),
                            "link": result.get('href'),
                            #"extracted_text": extracted_text
                        })
                    blob = f"Search results for '{prompt}' at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n\n"
                    template = "[{index}] \"{snippet}\"\nURL: {link}\n"
                    for i, result in enumerate(results_list):
                        blob += template.format(index=i, snippet=result["snippet"], link=result["link"])
                    blob +='\nPlease refer to the provided links before answering the user\'s query. These links are from an internet search related to the user\'s query.\n\n'
                    #print(blob)
                    
            else:
                blob = "No search query is needed for a response"
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
        response = f"Please provide a summary or additional information for the following YouTube video transcript in a few concise bullet points.\n\n{formatted_transcript}"
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
        response = f"The user has sent a URL.The following is the website contents. Please provide a reply or additional information."
        return response

    async def generate_keyboard(self,key):
        markup = ReplyKeyboardMarkup(row_width=5)
        if key == 'ratio':
            markup.add(*[KeyboardButton(x) for x in self._RATIO_OPTIONS.keys()])
        elif key == 'style':
            markup.add(*[KeyboardButton(x) for x in self._STYLE_OPTIONS.keys()])
        elif key == 'lang':
           markup.add(*(KeyboardButton(f"{self.lang['languages'][lang_code]}({lang_code})") for lang_code in self.lang['available_lang']))        
        return markup
    
