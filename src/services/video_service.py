from fastapi import UploadFile
import httpx
from src.config import settings

from src.models import SegmentTranscriptionModelWithWords

class VideoProcessingService:
    """A service that handles interactions with video processing tools."""

    def __init__(self):
        self.transcription_api = settings.TRANSCRIPTION_API_URL

    async def extract_transcript_with_timestamps(self, video_file: UploadFile) -> SegmentTranscriptionModelWithWords:
        """Extract the transcript of the video with timestamps."""
        file_bytes = await video_file.read()
        print(f"video_type: {video_file.content_type}")
        timeout = httpx.Timeout(500.0, connect=10.0)  # 60s write/read, 10s connect

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                files = {"media_file": (video_file.filename, file_bytes, video_file.content_type)}
                response = await client.post(self.transcription_api, files=files)
                response.raise_for_status()
                return SegmentTranscriptionModelWithWords(**(response.json()))
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            print("Error response body:", error_text)
            raise
