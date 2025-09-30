import uuid
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ImageTypeEnum(str, Enum):
    IMAGE = "image"
    CHART = "chart"
    TABLE = "table"


# Request schemas
class FileCreateSchema(BaseModel):
    file_type_id: uuid.UUID


class ImageCreateSchema(BaseModel):
    file_id: uuid.UUID
    image_title: str
    proposed_image_type: ImageTypeEnum
    is_protected: Optional[bool] = None
    searched_image_url: Optional[str] = Field(default=None)
    image_3d_url: Optional[str] = Field(default=None)
    description: str


# Response schemas (representing database models)


# GET types response schema
class GetTypeItemResponseSchema(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]


class GetTypesResponseSchema(BaseModel):
    result: List[GetTypeItemResponseSchema]


# Save file response schema
class FileResponseSchema(BaseModel):
    file_id: uuid.UUID = Field(alias="id")
    file_name: str
    file_type_id: uuid.UUID
    file_url: Optional[str]


# Save image response schema
class ImageResponseSchema(ImageCreateSchema):
    id: uuid.UUID
    original_image_url: str
