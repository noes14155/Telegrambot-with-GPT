import os
import tempfile
from gtts import gTTS
import requests
from pydub import AudioSegment

class TextToSpeech:
    def __init__(self, api_key: str, api_base: str, ):
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.api_base = api_base
        self.voice_id = "XB0fDUnXU5powFXDhCwa"
        response = requests.get(f"{self.api_base}/audio/tts/voices")
        self.use_openai_tts = response.status_code == 200

    async def text_to_speech(self, text, filename):
        if self.use_openai_tts:
            data = {
                "text": text,
                "voice_id": self.voice_id
            }
            response = requests.post(f"{self.api_base}/audio/tts",
                                     json=data,
                                     headers=self.headers)
            with open(filename, "wb") as f:
                f.write(response.content)
        else:
            tts = gTTS(text=text, lang='en')
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
                tts.save(temp_audio_path)
            os.rename(temp_audio_path, filename)
        return filename

    async def create_audio_segments(self, text, chunk_size=300):
        audio_filenames = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            audio_filename = f"audio_{i//chunk_size}.mp3"
            await self.text_to_speech(chunk, audio_filename)
            audio_filenames.append(audio_filename)
        return audio_filenames

    def join_audio_segments(self, audio_filenames, output_filename="output.mp3"):
        output = AudioSegment.empty()
        for filename in audio_filenames:
            segment = AudioSegment.from_file(filename)
            output += segment
            os.remove(filename)  # delete the chunk file
        output.export(output_filename, format="mp3")
        return output_filename