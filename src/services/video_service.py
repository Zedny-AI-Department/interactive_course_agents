import json
from typing import List
from fastapi import UploadFile
import httpx
from src.config import settings

from src.models import DetailedTranscription, ParagraphItem, MediaAlignmentResult


class VideoProcessingService:
    """A service that handles interactions with video processing tools."""

    def __init__(self):
        self.transcription_api = settings.TRANSCRIPTION_API_URL
        self.alignment_api = settings.ALIGNMENT_API_URL

    async def extract_transcript_with_timestamps(
        self, video_file: UploadFile
    ) -> DetailedTranscription:
        """Extract the transcript of the video with timestamps."""
        file_bytes = await video_file.read()
        timeout = httpx.Timeout(500.0, connect=10.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                files = {
                    "media_file": (
                        video_file.filename,
                        file_bytes,
                        video_file.content_type,
                    )
                }
                response = await client.post(self.transcription_api, files=files)
                response.raise_for_status()
                return DetailedTranscription(**(response.json()))
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            raise e

    async def align_paragraph_with_media(
        self, media_file: UploadFile, paragraphs: List[ParagraphItem]
    ) -> MediaAlignmentResult:
        """Extract the transcript of the video with timestamps."""
        file_bytes = await media_file.read()
        timeout = httpx.Timeout(500.0, connect=10.0)

        try:
            if not paragraphs:
                raise Exception("Paragraphs can't be empty")
            async with httpx.AsyncClient(timeout=timeout) as client:
                files = {
                    "media_file": (
                        media_file.filename,
                        file_bytes,
                        media_file.content_type,
                    )
                }
                paragraphs = [paragraph.model_dump() for paragraph in paragraphs]
                paragraphs_json = {"paragraphs": paragraphs}
                data = {"paragraphs_data": json.dumps(paragraphs_json)}
                headers = {"accept": "application/json"}
                response = await client.post(
                    url=self.alignment_api, headers=headers, files=files, data=data
                )
                response.raise_for_status()
                return MediaAlignmentResult(
                    aligned_paragraphs=response.json()["result"]
                )
        except httpx.HTTPStatusError as e:
            raise e
