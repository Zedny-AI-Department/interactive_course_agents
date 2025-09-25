"""Models for visual content including charts, images, and tables.

This module defines the structure for different types of visual content
that can be embedded within educational materials and synchronized with
timing information.
"""

from typing import Annotated, List, Literal, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from .base_models import StrictBaseModel


class TableContent(BaseModel):
    """Represents tabular data with headers and structured content.

    Used for displaying structured information in table format within
    educational content.

    Attributes:
        type: Always "table" for discriminator purposes
        headers: Column headers for the table
        data: Rows of data where each cell can be text or numeric
        title: Descriptive title for the table
        caption: Optional additional description
    """

    type: Literal["table"] = Field(
        default="table", description="Content type identifier"
    )
    headers: List[str] = Field(description="The headers of the table")
    data: List[List[str | int | float]] = Field(
        description="The data rows of the table"
    )
    title: str = Field(description="The title of the table")
    caption: Optional[str] = Field(default=None, description="Optional table caption")


class ChartDataset(BaseModel):
    """Dataset information for chart visualization.

    Contains the actual data points and labels needed to render
    various types of charts and graphs.

    Attributes:
        labels: X-axis labels or category names
        datasets: Y-axis data points or values
    """

    labels: List[str | int] = Field(description="Labels for the chart axes")
    datasets: List[float] = Field(description="Numerical data points for the chart")

    @field_validator("datasets", mode="before")
    def flatten_nested_datasets(cls, values: List) -> List[float]:
        """Flatten nested arrays to simple float values.

        Some data sources provide nested arrays like [[x, y]] but we only
        need the y values for most chart types.
        """
        if any(isinstance(item, list) for item in values):
            return [item[-1] if isinstance(item, list) else item for item in values]
        return values


class ChartContent(BaseModel):
    """Represents chart/graph data for visualization.

    Supports various chart types commonly used in educational content
    to display data relationships and trends.

    Attributes:
        type: Always "chart" for discriminator purposes
        chart_type: The specific type of chart to render
        data: The actual chart data and labels
        title: Descriptive title for the chart
    """

    type: Literal["chart"] = Field(
        default="chart", description="Content type identifier"
    )
    chart_type: Literal["bar", "line", "pie", "radar", "doughnut"] = Field(
        description="The specific type of chart visualization"
    )
    data: ChartDataset = Field(description="The chart data and labels")
    title: str = Field(description="The title of the chart")

    @field_validator("chart_type", mode="before")
    def ensure_valid_chart_type(cls, chart_type: str) -> str:
        """Ensure chart type is valid, default to line if invalid."""
        allowed_types = {"bar", "line", "pie", "radar", "doughnut"}
        return chart_type if chart_type in allowed_types else "line"


class ImageContent(BaseModel):
    """Represents image content with metadata.

    Used for static images that are part of the educational content,
    including proper accessibility attributes.

    Attributes:
        type: Always "image" for discriminator purposes
        url: Image URL or file path
        title: Descriptive title for the image
        alt_text: Accessibility text for screen readers
    """

    type: Literal["image"] = Field(
        default="image", description="Content type identifier"
    )
    url: str = Field(description="The URL or path to the image")
    title: str = Field(description="The title of the image")
    alt_text: Optional[str] = Field(
        default=None, description="Alternative text for accessibility"
    )


class VisualContent(BaseModel):
    """Container for any type of visual content with timing.

    This is the main visual content model that can contain any type
    of visual element (chart, image, or table) along with its timing
    information for synchronization with media.

    Attributes:
        type: The type of visual content contained
        content: The actual visual content (chart, image, or table)
        start_time: When this visual should appear (in seconds)
        assist_image_id: ID of the stored image for visual content
    """

    type: Literal["chart", "image", "table"] = Field(
        description="The type of visual content"
    )
    content: Annotated[
        Union[ChartContent, ImageContent, TableContent], Field(discriminator="type")
    ] = Field(description="The actual visual content")
    start_time: float = Field(description="When this visual appears in seconds")
    assist_image_id: Optional[UUID] = Field(default=None, description="ID of the stored image for visual content")


class ExtractedImage(BaseModel):
    """Raw image data extracted from PDF or other sources.

    Represents an image that has been extracted from a document
    before processing and analysis.

    Attributes:
        image_index: Sequential index of the extracted image
        image_bytes: Raw binary image data
        file_extension: Original file extension (png, jpg, etc.)
    """

    image_index: int = Field(description="Index of the extracted image")
    image_bytes: bytes = Field(description="Raw binary image data")
    file_extension: str = Field(description="File extension of the image")


class VisualMapping(StrictBaseModel):
    """Maps visual content to its descriptive information.

    Used to link extracted visual content with its generated
    descriptions and context information.

    Attributes:
        visual_index: Index reference to the visual content
        description: AI-generated description of the visual content
    """

    visual_index: int = Field(description="Index reference to the visual")
    description: str = Field(description="Description of the visual content")


class LLMImageContent(BaseModel):
    """Represents image content with metadata for LLM processing.

    Used for static images that are part of the educational content during
    LLM processing, before they are stored and get URLs.

    Attributes:
        type: Always "image" for discriminator purposes
        title: Descriptive title for the image
        alt_text: Accessibility text for screen readers
        url: Optional URL for the image (populated after storage)
    """

    type: Literal["image"] = Field(
        default="image", description="Content type identifier"
    )
    title: str = Field(description="The title of the image")
    alt_text: Optional[str] = Field(
        default=None, description="Alternative text for accessibility"
    )
    url: Optional[str] = Field(
        default=None, description="The URL of the image after storage"
    )


class LLMsearchedVisualContent(BaseModel):
    """Container for any type of visual content with timing.

    This is the main visual content model that can contain any type
    of visual element (chart, image, or table) along with its timing
    information for synchronization with media.

    Attributes:
        type: The type of visual content contained
        content: The actual visual content (chart, image, or table)
        visual_index: Index reference to the visual
        description: Description of the visual content
        assist_image_id: ID of the stored image for visual content
    """

    type: Literal["chart", "image", "table"] = Field(
        description="The type of visual content"
    )
    content: ChartContent | ImageContent | TableContent = Field(
        description="The actual visual content"
    )
    visual_index: int = Field(description="Index reference to the visual")
    description: str = Field(description="Description of the visual content")


class LLMVisualContentWithCopyright(LLMsearchedVisualContent):
    """Container for visual content with copyright assessment.

    Extended version of LLMsearchedVisualContent that includes copyright protection
    information for handling protected vs unprotected images.

    Attributes:
        type: The type of visual content contained
        content: The actual visual content (chart, image, or table)
        visual_index: Index reference to the visual
        description: Description of the visual content
        is_protected: Whether the content is protected by copyright
        assist_image_id: ID of the stored image for visual content
    """
    is_protected: bool = Field(description="Whether content is copyright protected")


class StoredVisualContent(LLMVisualContentWithCopyright):
    """Container for stored visual content with assist_image_id.

    This model represents visual content after it has been processed and stored,
    containing the assist_image_id for reference to the stored image.

    Attributes:
        type: The type of visual content contained
        content: The actual visual content (chart, image, or table)
        visual_index: Index reference to the visual
        description: Description of the visual content
        assist_image_id: ID of the stored image for visual content
        is_protected: Whether the content is protected by copyright (optional)
    """
    is_protected: Optional[bool] = Field(default=None, description="Whether content is copyright protected")
    assist_image_id: Optional[UUID] = Field(default=None, description="ID of the stored image for visual content")
