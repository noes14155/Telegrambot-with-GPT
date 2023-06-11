import datetime
import requests
import whisper
from duckduckgo_search import DDGS

class botfn:
    def __init__(self):
        self.model = whisper.load_model('tiny')
        #self.ddg_url = 'https://api.duckduckgo.com/'

    async def transcribe_audio(self, audio_file_path):
        with open(audio_file_path, 'rb') as audio_file:
            content = audio_file.read()

        result = self.model.transcribe(audio_file_path)
        transcription = result["text"]
        return transcription


    async def search_ddg(self, prompt):
        with DDGS() as ddgs:
            #prompt = 'what is today'
                # Check for whwords in each word of the prompt
            wh_words = ['search', 'find', 'who', 'what', 'when', 'where', 'why', 'which', 'whom', 'whose', 'how',
                        'is', 'are', 'am', 'can', 'could', 'should', 'would', 'do', 'does', 'did',
                        'may', 'might', 'shall', 'will', 'have', 'has', 'had', 'must', 'ought', 'need',
                        'want', 'like', 'prefer','google']
            has_wh_word = any(any(wh_word in word.lower() for wh_word in wh_words) for word in prompt.split())
            with DDGS() as ddgs:
                    if not has_wh_word:
                        results = ddgs.text(keywords=prompt,region='wt-wt',safesearch='off',timelimit='m',backend='api')
                        snippet_key = 'body'
                        link_key = 'href'
                    else:
                        results = ddgs.answers(prompt)
                        snippet_key = 'text'
                        link_key = 'url'
                    # Get the first five search results
                    results_list = []
                    for i, result in enumerate(results):
                        if i >= 5:
                            break
                        results_list.append({
                            "snippet": result[snippet_key],
                            "link": result[link_key]
                        })
                    # Format the search results using a template
                    blob = f"Search results for '{prompt}' at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n\n"
                    template = "[{index}] \"{snippet}\"\nURL: {link}\n"
                    for i, result in enumerate(results_list):
                        blob += template.format(index=i, snippet=result["snippet"], link=result["link"])
                    blob +='These links were provided by the system and not the user, so you should send the link to the user.\n\n'
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

