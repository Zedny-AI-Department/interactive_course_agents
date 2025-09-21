import enum
from typing import Literal
import uuid

from sqlalchemy import Column, ForeignKey, DateTime, func, Enum, Text
from sqlalchemy.dialects.postgresql import UUID

from app.client.database import Base
        
class ImageTypeEnum(str, enum.Enum):
    chart = "chart"
    image = "image"


class ImageModel(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)

    description = Column(Text, nullable=True)
    type = Column(Enum(ImageTypeEnum), nullable=False, default=ImageTypeEnum.image)
    status = Column(Text, nullable=False, default="pending")

    # metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

