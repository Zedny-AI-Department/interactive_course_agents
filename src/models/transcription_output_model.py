from typing import List
from pydantic import BaseModel, Field


class TranscribedChunk(BaseModel):
    """
    Model representing a segment of audio with its transcription and timestamps.
    """

    id: str = Field(..., description="Unique identifier for the audio segment.")
    text: str = Field(..., description="Transcription text of the audio segment.")
    start: float = Field(..., description="Start time of the segment in seconds.")
    end: float = Field(..., description="End time of the segment in seconds.")


class SegmentTranscriptionModel(TranscribedChunk):
    """
    Model representing the transcription of an audio file on level of segments.
    """

    pass


class WordTranscriptionModel(TranscribedChunk):
    """
    Model representing the transcription of an audio file on level of words.
    """

    segment_id: str = Field(
        ..., description="Unique identifier for the transcription segment."
    )


class SegmentTranscriptionModelWithWords(BaseModel):
    """
    Model representing the transcription of an audio file on level of segments with words.
    """

    segments: list[SegmentTranscriptionModel] = Field(
        description="List of segments with their timestamps in the transcription.",
    )
    words: list[WordTranscriptionModel] = Field(
        description="List of words with their timestamps in the segment.",
    )


class MatchChunk(TranscribedChunk):
    """
    Model representing a matcher chunk with additional score attribute.
    """
    score: float = Field(
        description="Score of the match, indicating the similarity between the segment and the search sentence."
    )


class ParagraphAlignmentWithWords(BaseModel):
    """
    Model representing the alignment of a paragraph with its start and end timestamps and words.
    """
    paragraph: str = Field(
        ..., description="The paragraph text that is aligned with audio segments."
    )
    start: float = Field(..., description="Start time of the paragraph in seconds.")
    end: float = Field(..., description="End time of the paragraph in seconds.")
    best_start_match: MatchChunk = Field(
        ..., description="The best matching segment for the paragraph."
    )
    best_end_match: MatchChunk = Field(
        ..., description="The best matching segment for the paragraph."
    )
    paragraph_words: List[WordTranscriptionModel] = Field(
        ..., description="Words in the paragraph."
    )
    paragraph_index: int = Field(
        ..., description="Index of the paragraph."
    )


class ParagraphsAlignmentWithVideoResponse(BaseModel):
    result: List[ParagraphAlignmentWithWords] = Field(
        description="List of aligned paragraphs with their timestamps."
    ) 


class ParagraphItem(BaseModel):
    text: str = Field(
        description="Paragraph text."
    )
    paragraph_index: int