from typing import Dict, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from src.models.base_models import TimestampedContent
from src.models.video_metadata_model import VideoMetadata


class MappedWord(BaseModel):
    word_type_id: UUID  # Reference to WordType by ID
    word: str
    start_time: float
    end_time: float


class MappedKeyWord(BaseModel):
    keyword_type_id: UUID
    word: str


class MappedTableData(BaseModel):
    headers: List[str]
    rows: List[List[str | int | float]]
    title: str
    caption: Optional[str]


class MappedChartData(BaseModel):
    chart_type_id: UUID  # Reference to ChartType by ID
    labels: List[str]  # Chart labels
    data: List[float]  # Chart data as list of floats or tuples
    title: str  # Chart title


class MappedImageData(BaseModel):
    image_type: Literal["2d_image"] = Field(..., description="Type of image (2D or 3D)")
    url: str
    title: str = Field(..., description="Image title")
    alt_text: Optional[str] = Field(default=None)


class MappedVisualContent(BaseModel):
    visual_type_id: UUID
    start_time: float
    table_data: Optional[MappedTableData] = Field(default=None)
    chart_data: Optional[MappedChartData] = Field(default=None)
    image_data: Optional[MappedImageData] = Field(default=None)
    assist_image_id: Optional[UUID] = Field(
        default=None,
        description="ID of existing assist image to link to this visual item",
    )


class MappedParagraph(TimestampedContent):
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

    view_index: int
    paragraph_text: str
    keywords: Optional[List[MappedKeyWord]] = Field(
        default=[], description="Key terms and concepts in the paragraph"
    )
    words: List[MappedWord] = Field(
        description="Precise timing information for each word"
    )
    visual_data: Optional[MappedVisualContent] = Field(
        default=None, description="Associated visual content"
    )


class MappedEducationalContent(BaseModel):
    """Complete educational content with all processed paragraphs.

    Represents the final output of the content processing pipeline,
    containing all paragraphs with their associated visual elements,
    timing information, and metadata.

    Attributes:
        paragraphs: List of fully processed paragraphs
        total_duration: Total duration of the content in seconds
        content_metadata: Additional metadata about the content
    """

    paragraphs: List[MappedParagraph] = Field(
        description="List of fully processed paragraphs"
    )
    video_metadata: Optional[VideoMetadata] = Field(
        description="Course information metadata"
    )
    assist_file_id: Optional[UUID] = None
    video_file_id: UUID
