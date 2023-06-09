import requests
import whisper
from duckduckgo_search import DDGS

class botfn:
    def __init__(self):
        self.model = whisper.load_model('tiny')
        self.ddg_url = 'https://api.duckduckgo.com/'

    async def transcribe_audio(self, audio_file_path):
        with open(audio_file_path, 'rb') as audio_file:
            content = audio_file.read()

        result = self.model.transcribe(audio_file_path)
        transcription = result["text"]
        return transcription


    async def search_ddg(self, query):
        with DDGS() as ddgs:
            results = ddgs.answers(query)

        result = []
        for r in results:
           result.append(r)
           if len(result)>5:
               break
        return result        
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
          # if len(result)>5:
          #     break
        return result