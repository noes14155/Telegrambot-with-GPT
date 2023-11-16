import re

from youtube_transcript_api import YouTubeTranscriptApi

class YoutubeTranscript:
    def get_transcript(self, video_id, lang_code):
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript([lang_code])
        if transcript is None:
            transcript = transcript_list.find_manually_created_transcript([lang_code])
        return transcript

    async def get_yt_transcript(self, message_content: str, lang: str) -> str:
        """
        Retrieves and formats the transcript of a YouTube video based on a given video URL.

        Args:
            message_content (str): The message content which includes a YouTube video URL.
            lang (str): The language parameter.

        Returns:
            str: The formatted transcript or None if an error occurs.
        """
        def extract_video_id(message_content: str) -> str:
            """
            Extracts the video ID from a YouTube video URL.

            Args:
                message_content (str): The message content which includes a YouTube video URL.

            Returns:
                str: The video ID or None if no match is found.
            """
            youtube_link_pattern = re.compile(
                r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
            )
            match = youtube_link_pattern.search(message_content)
            return match[6] if match else None

        try:
            video_id = extract_video_id(message_content)
            if not video_id:
                return None

            transcript = self.get_transcript(video_id, lang)

            #first_transcript = next(iter(transcript_list), None)
            if not transcript:
                return None

            formatted_transcript = ". ".join(
                [entry["text"] for entry in transcript.fetch()]
            )[:2500]

            response = f"Please provide a summary or additional information for the following YouTube video transcript in a few concise bullet points.\n\n{formatted_transcript}"
            return response
        except Exception as e:
            return None