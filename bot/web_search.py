from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup


class WebSearch:
    
 
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

 