import os

import aiogram.types as types
import speech_recognition as sr
from pydub import AudioSegment


class VoiceTranscript:
    def __init__(self):
        self.rec = sr.Recognizer()

    async def transcribe_audio(self, audio_file_path, lang):
        wav_file_path = audio_file_path.replace(".ogg", ".wav")
        audio = AudioSegment.from_ogg(audio_file_path)
        audio.export(wav_file_path, format="wav")
        with sr.AudioFile(wav_file_path) as audio_file:
            audio = self.rec.record(audio_file)
        transcription = self.rec.recognize_google(audio, language=f"{lang}")
        os.remove(wav_file_path)
        return transcription

    async def download_file(self, message: types.Message):
        if message.audio is not None:
            file = message.audio
            file_extension = (
                file.file_name.split(".")[-1] if file.file_name is not None else "ogg"
            )
        elif message.voice is not None:
            file = message.voice
            file_extension = "ogg"
        else:
            return None
        file_path = f"{file.file_id}.{file_extension}"
        file_dir = "downloaded_files"
        os.makedirs(file_dir, exist_ok=True)
        full_file_path = os.path.join(file_dir, file_path)
        await file.download(destination_file=full_file_path)
        return full_file_path
