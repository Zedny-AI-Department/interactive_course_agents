from typing import Annotated, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KeywordItemModel(StrictBaseModel):
    word: str = Field(description="The keyword word. can be consist of one up to 3 words")
    type: Literal["main", "Callouts", "Warnings", "Key Terms"]


class TableDataModel(StrictBaseModel):
    type: Literal["table"] = Field(default="table")
    headers: List[str] = Field(description="The headers of the table")
    data: List[List[str|int]] = Field(description="The data of the table")
    title: str = Field(description="The title of the table")
    caption: Optional[str] = Field(default=None, description="The caption of the table")


class ChartDataDetailsModel(StrictBaseModel):
    labels: List[str|int] = Field(
        description="Labels of the chart",
    )
    datasets: List[float] = Field(
        description="Datasets of the chart",
    )

    @field_validator("datasets", mode="before")
    def flatten_xy_to_y(cls, v: List):
        if any(isinstance(item, list) for item in v):
            return [item[-1] if isinstance(item, list) else item for item in v]
        return v

class ChartDataModel(StrictBaseModel):
    type: Literal["chart"] = Field(default="chart")
    chart_type: Literal["bar", "line", "pie", "radar", "doughnut"] = Field(
        description="The type of the chart"
    )
    data: ChartDataDetailsModel = Field(description="The data of the chart")
    title: str = Field(description="The title of the chart")
    
    @field_validator("chart_type", mode="before")
    def force_line_if_invalid(cls, v):
        allowed = {"bar", "line", "pie", "radar", "doughnut"}
        if v not in allowed:
            return "line"
        return v
    

class ImageModel(StrictBaseModel):
    type: Literal["image"] = Field(default="image")
    url: str = Field(description="The url of the image")
    title: str = Field(description="The title of the image")
    alt_text: Optional[str] = Field(
        description="The alt text of the image", default=None)


class GeneratedVisualItemModel(StrictBaseModel):
    type: Literal["chart", "image", "table"] = Field(
        description="The type of the item")
    content: Union[ChartDataModel, ImageModel, TableDataModel] = Field(
        description="The content of the item")
    start_sentence: str = Field(
        description="The start sentence of the item")


class GeneratedParagraphWithoutVisualModel(StrictBaseModel):
    paragraph_index: int = Field(description="The index of the paragraph")
    paragraph_text: str = Field(description="The text of the paragraph")
    keywords: Optional[List[KeywordItemModel]] = Field(
        description="The keywords of the paragraph", default=[]
    )


class GeneratedParagraphWithVisualModel(GeneratedParagraphWithoutVisualModel):
    visuals: Optional[GeneratedVisualItemModel] = Field(
        description="The visuals of the paragraph"
    )


class GeneratedParagraphWithVisualListModel(StrictBaseModel):
    paragraphs: List[GeneratedParagraphWithVisualModel] = Field(
        description="List of paragraphs")


class GeneratedVisualMappingModel(StrictBaseModel):
    visual_index: int
    visual_description: str
    start_sentence: str = Field(
        description="The start sentence of the item")


class GeneratedParagraphVisualAlignmentModel(GeneratedParagraphWithoutVisualModel):
    visuals: Optional[GeneratedVisualMappingModel] = Field(
        description="The visuals of the paragraph"
    )
    

class GeneratedParagraphsVisualAlignmentModel(StrictBaseModel):
    paragraphs: List[GeneratedParagraphVisualAlignmentModel] = Field(
        description="List of paragraphs")