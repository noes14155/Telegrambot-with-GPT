from typing import Optional
from aiogram import types
import os
import aiogram.types as types
import speech_recognition as sr
from pydub import AudioSegment

class VoiceTranscript:
    """
    The `VoiceTranscript` class is responsible for transcribing audio files using the Google Speech Recognition API.
    It provides methods for downloading audio files and transcribing them into text.
    """

    def __init__(self):
        self.rec = sr.Recognizer()

    async def transcribe_audio(self, audio_file_path: str, lang: str) -> str:
        """
        Transcribes an audio file into text.

        Args:
            audio_file_path (str): The path of the audio file.
            lang (str): The language code.

        Returns:
            str: The transcription of the audio file.
        """
        try:
            wav_file_path = audio_file_path.replace(".ogg", ".wav")
            audio = AudioSegment.from_ogg(audio_file_path)
            audio.export(wav_file_path, format="wav")

            with sr.AudioFile(wav_file_path) as audio_file:
                audio = self.rec.record(audio_file)

            transcription = self.rec.recognize_google(audio, language=lang)
            os.remove(wav_file_path)

        except Exception as e:
            transcription = f"Error during audio transcription: {str(e)}"

        return transcription

    async def download_file(self, bot, message: types.Message) -> Optional[str]:
        """
        Downloads an audio file from a message using a Telegram bot.

        Args:
            bot: The Telegram bot instance.
            message (types.Message): The message containing the audio file.

        Returns:
            Optional[str]: The path of the downloaded file, or None if an error occurs during the download.
        """
        try:
            if message.audio is not None:
                file = message.audio
                file_extension = file.file_name.split(".")[-1] if file.file_name is not None else "ogg"
            elif message.voice is not None:
                file = message.voice
                file_extension = "ogg"
            else:
                return None

            file_path = f"{file.file_id}.{file_extension}"
            file_dir = "downloaded_files"
            os.makedirs(file_dir, exist_ok=True)
            full_file_path = os.path.join(file_dir, file_path)

            await bot.download(file=file, destination=full_file_path)
            return full_file_path

        except Exception as e:
            print(f"Error during file download: {str(e)}")
            return None
