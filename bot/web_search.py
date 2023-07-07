import datetime
import re
from urllib.parse import urlparse

import requests
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from readability import Document
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class WebSearch:
    def __init__(self, lang):
        self.lang = lang

    async def search_ddg(self, prompt):
        with DDGS() as ddgs:
            if re.search(r"(https?://\S+)", prompt) or len(prompt) > 1000:
                return
            if prompt is not None:
                results = ddgs.text(
                    keywords=prompt, region="wt-wt", safesearch="off", backend="api"
                )
                results_list = []
                for i, result in enumerate(results):
                    if i >= 3:
                        break
                    results_list.append(
                        {
                            "snippet": result.get("body"),
                            "link": result.get("href"),
                        }
                    )
                blob = f"Search results for '{prompt}' at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n\n"
                template = '[{index}] "{snippet}"\nURL: {link}\n'
                for i, result in enumerate(results_list):
                    blob += template.format(
                        index=i, snippet=result["snippet"], link=result["link"]
                    )
                blob += "\nPlease refer to the provided links before answering the user's query. These links are from an internet search related to the user's query.\n\n"
                # print(blob)

            else:
                blob = "No search query is needed for a response"
            return blob

    async def news_ddg(self, prompt="latest world news"):
        with DDGS() as ddgs:
            if prompt is not None:
                results = ddgs.text(keywords=prompt, region="wt-wt", safesearch="off")
                results_list = []
                for i, result in enumerate(results):
                    if i >= 3:
                        break
                    results_list.append(
                        {
                            "snippet": result.get("body"),
                            "link": result.get("href"),
                        }
                    )
                blob = f"News results for '{prompt}' at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n\n"
                template = '[{index}] "{snippet}"\nURL: {link}\n'
                for i, result in enumerate(results_list):
                    blob += template.format(
                        index=i, snippet=result["snippet"], link=result["link"]
                    )
                blob += "\nThese are the latest news articles related to the user's query. Provide a summary or analysis of the news articles related to the user's query.\
                      Respond to the user's query using the information from the provided links.\
                      Avoid mentioning that you are an AI language model or that you lack access to the latest information.\n\n"
            else:
                blob = "No search query is needed for a response"
            return blob

    async def extract_text_from_website(self, url):
        parsed_url = urlparse(url)
        if parsed_url.scheme == "" or parsed_url.netloc == "":
            return None
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
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
            extracted_text = re.sub("<[^<]+?>", "", extracted_html)
            if not extracted_text.strip():
                extracted_text = None
            driver.quit()
        response = f"The user has sent a URL.The following is the website contents. Please provide a reply or additional information." + extracted_text
        return response

    async def generate_keyboard(self, key):
        markup = ReplyKeyboardMarkup(row_width=5)
        if key == "lang":
            markup.add(
                *(
                    KeyboardButton(f"{self.lang['languages'][lang_code]}({lang_code})")
                    for lang_code in self.lang["available_lang"]
                )
            )
        return markup

    async def generate_query(self, response, plugins_dict):
        opening_bracket = response.find("[")
        closing_bracket = response.find("]")

        if opening_bracket != -1 and closing_bracket != -1:
            plugin_text = response[opening_bracket + 1 : closing_bracket]
            plugin_parts = plugin_text.split()
            plugin_name = plugin_parts[0]
            query = " ".join(plugin_parts[1:])

            if plugin_name is not None and query is not None:
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
        else:
            return None, None
