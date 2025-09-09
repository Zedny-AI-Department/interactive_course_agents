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
