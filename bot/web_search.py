import datetime
import re
from urllib.parse import urlparse
import aiohttp
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from itertools import islice
import wolframalpha

class WebSearch:
    
        

    async def ddg_search(self, prompt, template_message, news=False):
        if not isinstance(prompt, str) or not isinstance(template_message, str):
            raise ValueError("prompt and template_message must be strings")

        with DDGS() as ddgs:
            if re.search(r"(https?://\S+)", prompt) or len(prompt) > 1000:
                return
            if prompt:
                results = ddgs.text(
                    keywords=prompt, region="wt-wt", safesearch="off", backend="api"
                ) if not news else ddgs.news(keywords=prompt, region="wt-wt", safesearch="off")
                results_list = [result for result in islice(results, 3)]
                blob = f"{template_message.format(prompt)} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n\n"
                template = '[{index}] "{snippet}"\nURL: {link}\n'
                if news:
                    body = 'title'
                    href = 'url'
                else:
                    body = 'body'
                    href = 'href'
                    
                for i, result in enumerate(results_list):
                    blob += template.format(
                        index=i, snippet=result[body], link=result[href]
                    )
                return blob
            else:
                return "No search query is needed for a response"
            
    async def search_ddg(self, prompt):
        return await self.ddg_search(prompt, "Search results for '{}'")

    async def news_ddg(self, prompt="latest world news"):
        return await self.ddg_search(prompt, "News results for '{}'", news=True)

    async def extract_text_from_website(self, url):
        if not isinstance(url, str):
            raise ValueError("url must be a string")

        parsed_url = urlparse(url)
        if parsed_url.scheme == "" or parsed_url.netloc == "":
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    content = await response.text()
                    soup = BeautifulSoup(content, "html.parser")
                    extracted_text = soup.get_text()
                    return extracted_text.strip() or None
        except Exception as e:
            print(f"Failed to extract text from website: {e}")
            return None

  

    async def generate_query(self, response, plugins_dict):
        if not isinstance(response, str) or not isinstance(plugins_dict, dict):
            raise ValueError("response must be a string and plugins_dict must be a dict")
        lines = response.split('\n')
        plugin_name = None
        query = None
        for line in lines:
            if "Plugin:" in line:
                plugin_name = line.split(":")[1].strip()
                if plugin_name in plugins_dict.keys():
                    for next_line in lines[lines.index(line) + 1:]:
                        if "Query:" in next_line:
                            query = next_line.split(":")[1].strip()
                            break
                        
                    if query is not None:
                        break
        if plugin_name and query:
            if plugin_name.lower() == "wolframalpha":
                return (
                    "wolframalpha plugin is not yet implemented so provide a response yourself",
                    plugin_name,
                )
            elif plugin_name.lower() == "duckduckgosearch":
                return await self.search_ddg(query), plugin_name
            elif plugin_name.lower() == "duckduckgonews":
                return await self.news_ddg(query), plugin_name
            else:
                return None, None
        else:
            return None, None
        