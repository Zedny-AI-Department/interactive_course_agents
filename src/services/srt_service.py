from fastapi import UploadFile
import srt


class SRTProcessingService:
    """A service that handles interactions with SRT processing tools."""

    def __init__(self):
        # Initialize any required resources, e.g., loading models or setting up configurations
        pass

    async def extract_text(self, srt_file: UploadFile) -> str:
        """Extract text from the SRT file."""
        # Process the SRT file to extract the text content.
        srt_content = await srt_file.read()
        # Convert the SRT content to text
        subtitles = list(srt.parse(srt_content.decode("utf-8")))
        text = " ".join([subtitle.content.replace("\n", " ") for subtitle in subtitles])
        return text
