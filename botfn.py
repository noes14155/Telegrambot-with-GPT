import requests
import whisper


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
        params = {
            'q': query,
            'format': 'json',
            'no_redirect': '1',
        }
        response = await requests.get(self.ddg_url, params=params)
        if response.status_code == 200:
            results = response.json()['Results']
            if len(results) > 0:
                result_strs = []
                for result in results:
                    result_strs.append(f'{result["Text"]}\n{result["FirstURL"]}')
                return '\n\n'.join(result_strs)
            else:
                return 'No results found.'
        else:
            return 'Error searching DuckDuckGo.'
