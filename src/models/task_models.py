from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStage(str, Enum):
    QUEUED = "queued"
    TRANSCRIBING = "transcribing"
    PROCESSING_LLM = "processing_llm"
    ALIGNING = "aligning"
    COMPLETED = "completed"


class AgentMode(str, Enum):
    GENERATE = "generate"
    ALWAYS_SEARCH = "always_search"
    SEARCH_FOR_COPYRIGHT = "search_for_copyright"


class VideoMetadata(BaseModel):
    course_id: str = Field(..., description="Course identifier")
    chapter_id: str = Field(..., description="Chapter identifier")
    video_name: str = Field(..., description="Video name")
    agent_mode: AgentMode = Field(..., description="Processing mode used")


class TaskData(BaseModel):
    task_id: str
    user_id: str
    status: TaskStatus
    stage: TaskStage
    progress: int = Field(default=0, ge=0, le=100)
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    video_metadata: VideoMetadata
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    task_id: str
    user_id: str
    status: TaskStatus
    stage: TaskStage
    progress: int
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    video_metadata: VideoMetadata
    metadata: Optional[Dict[str, Any]] = None


class CreateTaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str


class UserTasksResponse(BaseModel):
    user_id: str
    active_tasks: list[TaskResponse]
    completed_tasks: list[TaskResponse]
    total_active: int
    total_completed: int