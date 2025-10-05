from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class AgentMode(str, Enum):
    GENERATE = "generate"
    ALWAYS_SEARCH = "always_search"
    SEARCH_FOR_COPYRIGHT = "search_for_copyright"


class VideoMetadataRequest(BaseModel):
    course_id: UUID = Field(..., description="Course identifier")
    chapter_id: UUID = Field(..., description="Chapter identifier")
    title: str = Field(..., description="Video name")
    agent_mode: AgentMode = Field(..., description="Processing mode used")
    view_index: int


class VideoMetadata(VideoMetadataRequest):
    video_duration: str
