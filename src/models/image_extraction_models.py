from typing import List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class ExtractedImageModel(BaseModel):
    img_index: int
    img_bytes: bytes
    img_extension: str


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TableDataModel(BaseModel):
    type: Literal["table"] = Field(default="table")
    headers: List[str] = Field(description="The headers of the table")
    data: List[List[str | float]] = Field(description="The data of the table")
    title: str = Field(description="The title of the table")
    caption: Optional[str] = Field(default=None, description="The caption of the table")


class ChartDataDetailsModel(BaseModel):
    type: Literal["chart"] = Field(default="chart")
    labels: List[str | int] = Field(description="Labels of the chart")
    datasets: List[float] = Field(description="Datasets of the chart")


class ChartDataModel(BaseModel):
    chart_type: Literal["bar", "line", "pie", "radar", "doughnut"] = Field(
        description="The type of the chart"
    )
    data: ChartDataDetailsModel = Field(description="The data of the chart")
    title: str = Field(description="The title of the chart")


class DescribedImageModel(BaseModel):
    type: Literal["image"] = Field(default="image")
    title: str = Field(description="The title of the image")
    alt_text: Optional[str] = Field(
        description="The alt text of the image", default=None
    )


class DescribedVisualModel(BaseModel):
    visual_index: int = Field(description="index of image")
    type: Literal["chart", "image", "table"] = Field(description="The type of the item")
    content: Union[ChartDataModel, DescribedImageModel, TableDataModel] = Field(
        description="The content of the item"
    )
    description: str = Field(description="The description of the image")


class ImageModel(DescribedImageModel):
    type: Literal["image"] = Field(default="image")
    url: str = Field(description="Image URL")
    title: str = Field(description="The title of the image")
    alt_text: Optional[str] = Field(
        description="The alt text of the image", default=None
    )



class SearchedImageVisualModel(BaseModel):
    visual_index: int = Field(description="index of image")
    type: Literal["chart", "image", "table"] = Field(description="The type of the item")
    content: Union[ChartDataModel, ImageModel, TableDataModel] = Field(
        description="The content of the item"
    )
    description: str = Field(description="The description of the image")


class VisualMappingModel(StrictBaseModel):
    visual_index: int
    visual_description: str