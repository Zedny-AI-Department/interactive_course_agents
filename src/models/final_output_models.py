"""Final output models for processed educational content.

This module contains the final data structures that represent the complete
processed educational content ready for consumption by frontend applications
or export to various formats.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from .base_models import KeywordItem, WordTimestamp, TimestampedContent
from .visual_content_models import VisualContent
from src.models.video_metadata_model import VideoMetadata


class ProcessedParagraph(TimestampedContent):
    """Complete paragraph with all processed information.

    Represents a fully processed paragraph that includes text content,
    timing information, keywords, word-level timestamps, and any
    associated visual content.

    Attributes:
        paragraph_id: Unique identifier for the paragraph
        text_content: The paragraph text
        keywords: Important terms and concepts
        word_timestamps: Precise timing for each word
        visual_content: Optional associated visual element
    """

    paragraph_id: int = Field(description="Unique identifier for the paragraph")
    text_content: str = Field(description="The paragraph text content")
    keywords: Optional[List[KeywordItem]] = Field(
        default=[], description="Key terms and concepts in the paragraph"
    )
    word_timestamps: List[WordTimestamp] = Field(
        description="Precise timing information for each word"
    )
    visual_content: Optional[VisualContent] = Field(
        default=None, description="Associated visual content"
    )

    # Backward compatibility aliases
    @property
    def paragraph_text(self) -> str:
        """Alias for text_content to maintain backward compatibility."""
        return self.text_content

    @property
    def words(self) -> List[dict]:
        """Convert word timestamps to dict format for backward compatibility."""
        return [
            {"word": word.word, "start": word.start, "end": word.end}
            for word in self.word_timestamps
        ]
    

    @property
    def visuals(self) -> Optional[dict]:
        """Convert visual content to dict format for backward compatibility."""
        return self.visual_content.model_dump() if self.visual_content else None


class EducationalContent(BaseModel):
    """Complete educational content with all processed paragraphs.

    Represents the final output of the content processing pipeline,
    containing all paragraphs with their associated visual elements,
    timing information, and metadata.

    Attributes:
        paragraphs: List of fully processed paragraphs
        total_duration: Total duration of the content in seconds
        content_metadata: Additional metadata about the content
    """

    paragraphs: List[ProcessedParagraph] = Field(
        description="List of fully processed paragraphs"
    )
    video_metadata: Optional[VideoMetadata] = Field(
        description="Course information metadata"
    )
    assist_file_id: Optional[UUID] = None
    video_file_id: UUID