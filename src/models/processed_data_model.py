from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field


class KeywordItemModel(BaseModel):
    word: str
    type: Literal["main", "Callouts", "Warnings", "Key Terms"]


class WordTimestampModel(BaseModel):
    word: str
    start: float
    end: float


class TableDataModel(BaseModel):
    headers: List[str]
    data: List[List[str]]
    title: str
    caption: Optional[str] = None


class ChartDataDetailsModel(BaseModel):
    labels: List[str] = Field(
        description="Labels of the chart",
    )
    datasets: List[float] = Field(
        description="Datasets of the chart",
    )


class ChartDataModel(BaseModel):
    type: Literal["bar", "line", "pie", "radar", "doughnut"]
    data: ChartDataDetailsModel
    title: str


class ImageModel(BaseModel):
    url: str
    title: str
    alt_text: Optional[str] = None


class VisualItemModel(BaseModel):
    type: Literal["chart", "image", "table"]
    content: Union[ChartDataModel, ImageModel, TableDataModel]
    start_time: float


class ParagraphWithoutVisualModel(BaseModel):
    paragraph_id: int
    paragraph_text: str
    start_time : float
    end_time: float
    keywords: Optional[List[KeywordItemModel]] = []
    words: List[WordTimestampModel]


class ParagraphWithVisualModel(ParagraphWithoutVisualModel):
    visuals: VisualItemModel


class ParagraphWithVisualListModel(BaseModel):
    paragraphs: List[ParagraphWithVisualModel] = []

