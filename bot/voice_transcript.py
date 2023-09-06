from typing import Optional
from telebot import types
import os
import asyncio
import aiogram.types as types
import speech_recognition as sr
from pydub import AudioSegment

class VoiceTranscript:
    """
    The `VoiceTranscript` class is responsible for transcribing audio files using the Google Speech Recognition API.
    It provides methods to download audio files, convert them to the required format, and transcribe the audio content.
    """

    def __init__(self):
        self.rec = sr.Recognizer()

    async def transcribe_audio(self, audio_file_path: str, lang: str) -> Optional[str]:
        """
        Converts the audio file to WAV format, transcribes the audio content using the Google Speech Recognition API,
        and returns the transcription as a string.
        :param audio_file_path: The path of the audio file to transcribe.
        :param lang: The language code for the transcription.
        :return: The transcription as a string, or None if there was an error during transcription.
        """
        try:
            wav_file_path = audio_file_path.replace(".ogg", ".wav")
            audio = AudioSegment.from_ogg(audio_file_path)
            audio.export(wav_file_path, format="wav")
            with sr.AudioFile(wav_file_path) as audio_file:
                audio = self.rec.record(audio_file)
            transcription = self.rec.recognize_google(audio, language=f"{lang}")
            os.remove(wav_file_path)
            return transcription
        except Exception as e:
            print(f"Error during audio transcription: {str(e)}")
            return None

    async def download_file(self, message: types.Message) -> Optional[str]:
        """
        Downloads the audio file specified in the `message` object and returns the file path as a string.
        :param message: The message object containing the audio file.
        :return: The file path as a string, or None if there was an error during file download.
        """
        try:
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
        except Exception as e:
            print(f"Error during file download: {str(e)}")
            return None