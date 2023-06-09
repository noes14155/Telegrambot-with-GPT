from bot import botfn
import asyncio

from duckduckgo_search import DDGS

with DDGS() as ddgs:
    for r in ddgs.answers("sun"):
        print(r['url'])

with DDGS() as ddgs:
    keywords = 'latest world news'
    ddgs_news_gen = ddgs.news(
      keywords,
      region="wt-wt",
      safesearch="Off",
      timelimit="m",
    )
    for r in ddgs_news_gen:
        print(r)