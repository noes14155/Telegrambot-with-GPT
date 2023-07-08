import re

from youtube_transcript_api import YouTubeTranscriptApi

class YoutubeTranscript:
    async def get_yt_transcript(self, message_content, lang):
        def extract_video_id(message_content):
            youtube_link_pattern = re.compile(
                r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
            )
            match = youtube_link_pattern.search(message_content)
            return match.group(6) if match else None
        try:
            video_id = extract_video_id(message_content)
            if not video_id:
                return None
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            first_transcript = next(iter(transcript_list), None)
            if not first_transcript:
                return None
            # translated_transcript = first_transcript.translate(f"{lang}")
            formatted_transcript = ". ".join(
                [entry["text"] for entry in first_transcript.fetch()]
            )[:2500]
            response = f"Please provide a summary or additional information for the following YouTube video transcript in a few concise bullet points.\n\n{formatted_transcript}"
            return response
        except Exception as e:
            return None