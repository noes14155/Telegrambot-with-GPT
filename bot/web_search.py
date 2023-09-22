from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup


class WebSearch:
    """
    The `WebSearch` class is responsible for extracting text from a given website URL using asynchronous HTTP requests and web scraping techniques.
    """

    async def extract_text_from_website(self, url: str) -> str:
        """
        Extracts the text content from the website asynchronously.

        Args:
            url (str): The URL of the website to extract text from.

        Returns:
            str: The extracted text content from the website, or None if the URL is invalid or an exception occurs.
        """
        if not isinstance(url, str):
            raise ValueError("url must be a string")

        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
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

 