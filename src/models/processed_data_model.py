from typing import Annotated, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


class KeywordItemModel(BaseModel):
    word: str
    type: Literal["main", "Callouts", "Warnings", "Key Terms"]


class WordTimestampModel(BaseModel):
    word: str
    start: float
    end: float


class TableDataModel(BaseModel):
    type: Literal["table"] = Field(default="table")
    headers: List[str]
    data: List[List[str|int]]
    title: str
    caption: Optional[str] = None


class ChartDataDetailsModel(BaseModel):
    labels: List[str|int] = Field(
        description="Labels of the chart",
    )
    datasets: List[float] = Field(
        description="Datasets of the chart",
    )


class ChartDataModel(BaseModel):
    type: Literal["chart"] = Field(default="chart")
    chart_type: Literal["bar", "line", "pie", "radar", "doughnut"]
    data: ChartDataDetailsModel
    title: str


class ImageModel(BaseModel):
    type: Literal["image"] = Field(default="image")
    url: str
    title: str
    alt_text: Optional[str] = None


class VisualItemModel(BaseModel):
    type: Literal["chart", "image", "table"]
    content: Annotated[
    Union[ChartDataModel, ImageModel, TableDataModel],
        Field(discriminator="type")
    ]
    start_time: float


class ParagraphWithoutVisualModel(BaseModel):
    paragraph_id: int
    paragraph_text: str
    start_time : float
    end_time: float
    keywords: Optional[List[KeywordItemModel]] = []
    words: List[WordTimestampModel]


class ParagraphWithVisualModel(ParagraphWithoutVisualModel):
    visuals: Optional[VisualItemModel]


class ParagraphWithVisualListModel(BaseModel):
    paragraphs: List[ParagraphWithVisualModel] = []

