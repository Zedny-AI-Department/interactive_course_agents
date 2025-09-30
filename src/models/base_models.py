"""Base models and shared components for the data processing system.

This module contains foundational models that are reused across different parts
of the application to ensure consistency and avoid duplication.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Base model with strict validation that forbids extra fields."""

    model_config = ConfigDict(extra="forbid")


class KeywordItem(BaseModel):
    """Represents a keyword or key phrase with its classification type.

    Keywords are used to highlight important concepts within paragraphs
    and can be categorized by their semantic importance.

    Attributes:
        word: The keyword or phrase (can be 1-3 words)
        type: Classification of the keyword's importance level
    """

    word: str = Field(
        description="The keyword word. can be consist of one up to 3 words"
    )
    type: Literal["main", "Callouts", "Warnings", "Key Terms"] = Field(
        description="The type/category of the keyword"
    )


class WordTimestamp(BaseModel):
    """Represents a word with its precise timing information.

    Used for synchronizing text with audio/video content at the word level
    for accurate subtitle and timing alignment.

    Attributes:
        word: The actual word text
        start: Start time in seconds
        end: End time in seconds
    """

    word: str = Field(description="The word text")
    start: float = Field(description="Start time of the word in seconds")
    end: float = Field(description="End time of the word in seconds")
    word_type: Literal["text"]


class TimestampedContent(BaseModel):
    """Base class for content that has timing information.

    Provides common timing attributes for any content that needs
    to be synchronized with media files.

    Attributes:
        start_time: When the content begins (in seconds)
        end_time: When the content ends (in seconds)
    """

    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")
