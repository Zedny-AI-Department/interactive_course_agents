"""Models for audio/video transcription and timing alignment.

This module handles the output from transcription services and provides
structures for aligning text content with precise audio/video timestamps.
"""

from typing import List
from pydantic import BaseModel, Field

from .base_models import TimestampedContent, WordTimestamp


class TranscribedSegment(TimestampedContent):
    """Base class for transcribed audio/video segments.

    Represents a portion of audio or video content that has been
    transcribed to text with precise timing information.

    Attributes:
        id: Unique identifier for this segment
        text: The transcribed text content
        start_time: When the segment begins (inherited)
        end_time: When the segment ends (inherited)
    """

    id: str = Field(description="Unique identifier for the audio segment")
    text: str = Field(description="Transcribed text of the audio segment")

    # Override inherited fields with more specific names for backward compatibility
    start: float = Field(description="Start time of the segment in seconds")
    end: float = Field(description="End time of the segment in seconds")

    @property
    def start_time(self) -> float:
        """Alias for start to maintain interface compatibility."""
        return self.start

    @property
    def end_time(self) -> float:
        """Alias for end to maintain interface compatibility."""
        return self.end


class AudioSegment(TranscribedSegment):
    """Represents a complete audio segment with transcription.

    This is the primary segment-level transcription model used for
    organizing transcribed content into meaningful chunks.
    """

    pass


class WordTranscription(TranscribedSegment):
    """Represents a single word with precise timing information.

    Provides word-level granularity for transcription data, enabling
    precise synchronization of individual words with media content.

    Attributes:
        segment_id: ID of the parent segment this word belongs to
    """

    segment_id: str = Field(description="ID of the parent segment containing this word")


class DetailedTranscription(BaseModel):
    """Complete transcription with both segment and word-level timing.

    Provides comprehensive transcription data that includes both
    segment-level organization and word-level precision timing.

    Attributes:
        segments: List of transcribed segments with timestamps
        words: List of individual words with precise timestamps
    """

    segments: List[AudioSegment] = Field(
        description="List of transcribed segments with timing information"
    )
    words: List[WordTranscription] = Field(
        description="List of individual words with precise timestamps"
    )


class ScoredMatch(TranscribedSegment):
    """Transcribed segment with similarity matching score.

    Used for alignment algorithms that need to find the best matching
    segments based on text similarity or other criteria.

    Attributes:
        score: Confidence score for the match quality (0.0 to 1.0)
    """

    score: float = Field(
        description="Similarity score indicating match quality (0.0 to 1.0)"
    )


class AlignedParagraph(TimestampedContent):
    """Paragraph aligned with audio/video timing and word-level data.

    Represents a paragraph that has been successfully aligned with
    media content, including precise timing and word-level breakdown.

    Attributes:
        paragraph: The paragraph text content
        paragraph_index: Sequential index of this paragraph
        best_start_match: Highest scoring match for paragraph start
        best_end_match: Highest scoring match for paragraph end
        word_details: Individual words with their timestamps
    """

    paragraph: str = Field(description="The aligned paragraph text")
    paragraph_index: int = Field(description="Sequential index of the paragraph")
    best_start_match: ScoredMatch = Field(
        description="Best matching segment for paragraph start"
    )
    best_end_match: ScoredMatch = Field(
        description="Best matching segment for paragraph end"
    )
    word_details: List[WordTranscription] = Field(
        description="Individual words with precise timestamps", alias="paragraph_words"
    )

    # Override inherited fields with more specific names for backward compatibility
    start: float = Field(description="Start time of the paragraph in seconds")
    end: float = Field(description="End time of the paragraph in seconds")

    @property
    def start_time(self) -> float:
        """Alias for start to maintain interface compatibility."""
        return self.start

    @property
    def end_time(self) -> float:
        """Alias for end to maintain interface compatibility."""
        return self.end

    @property
    def paragraph_words(self) -> List[WordTranscription]:
        """Alias for word_details to maintain backward compatibility."""
        return self.word_details


class MediaAlignmentResult(BaseModel):
    """Result of paragraph alignment with media content.

    Contains the complete result of aligning multiple paragraphs
    with audio or video content, including timing information.

    Attributes:
        aligned_paragraphs: List of successfully aligned paragraphs
    """

    aligned_paragraphs: List[AlignedParagraph] = Field(
        description="List of paragraphs aligned with media timing"
    )

    @property
    def result(self) -> List[AlignedParagraph]:
        """Alias for aligned_paragraphs to maintain backward compatibility."""
        return self.aligned_paragraphs


class ParagraphItem(BaseModel):
    """Simple paragraph representation for processing workflows.

    A lightweight model used for intermediate processing steps
    where only basic paragraph information is needed.

    Attributes:
        text: The paragraph text content
        paragraph_index: Sequential index of the paragraph
    """

    text: str = Field(description="The paragraph text content")
    paragraph_index: int = Field(description="Sequential index of the paragraph")
