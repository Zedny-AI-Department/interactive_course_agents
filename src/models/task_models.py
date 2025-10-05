from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum

from src.models.video_metadata_model import VideoMetadata

# Task Enums
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


# Task Models

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
    video_metadata: Optional[VideoMetadata] = None
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