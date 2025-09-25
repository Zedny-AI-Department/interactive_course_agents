import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

from src.services.redis_service import redis_service
from src.models.task_models import TaskData, TaskStatus, TaskStage, TaskResponse
from src.config import settings


class TaskManagerService:
    """Service for managing background tasks with Redis storage."""
    
    def __init__(self):
        self.redis = None
    
    async def _get_redis(self):
        """Get Redis connection."""
        if not self.redis:
            self.redis = await redis_service.get_redis()
        return self.redis
    
    async def create_task(self, user_id: str, task_type: Optional[str] = "process_data") -> str:
        """Create a new background task for a user."""
        redis_client = await self._get_redis()
        
        # Check user concurrent task limit
        active_tasks = await self.get_user_active_tasks(user_id)
        if len(active_tasks) >= settings.MAX_CONCURRENT_TASKS_PER_USER:
            raise HTTPException(
                status_code=429, 
                detail=f"Maximum {settings.MAX_CONCURRENT_TASKS_PER_USER} concurrent tasks per user exceeded"
            )
        
        # Check global concurrent task limit
        global_active = await redis_client.get("global:active_tasks_count") or "0"
        if int(global_active) >= settings.MAX_GLOBAL_CONCURRENT_TASKS:
            raise HTTPException(
                status_code=503, 
                detail="Server is busy, please try again later"
            )
        
        # Generate task ID
        task_id = f"{user_id}:{uuid.uuid4().hex}"
        
        # Create task data
        now = datetime.utcnow()
        task_data = TaskData(
            task_id=task_id,
            user_id=user_id,
            status=TaskStatus.PENDING,
            stage=TaskStage.QUEUED,
            progress=0,
            created_at=now,
            updated_at=now
        )
        
        # Store in Redis atomically
        pipe = redis_client.pipeline()
        pipe.hset(f"task:{task_id}", "data", task_data.model_dump_json())
        pipe.sadd(f"user:{user_id}:active_tasks", task_id)
        pipe.incr("global:active_tasks_count")
        pipe.expire(f"task:{task_id}", 86400)  # 24 hour expiry
        await pipe.execute()
        
        return task_id
    
    async def update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus, 
        stage: TaskStage = None, 
        progress: int = None,
        result: Dict[str, Any] = None,
        error_message: str = None
    ):
        """Update task status and progress."""
        redis_client = await self._get_redis()
        
        # Get current task data
        task_json = await redis_client.hget(f"task:{task_id}", "data")
        if not task_json:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task_data = TaskData.model_validate_json(task_json)
        
        # Update fields
        task_data.status = status
        if stage:
            task_data.stage = stage
        if progress is not None:
            task_data.progress = progress
        if result is not None:
            task_data.result = result
        if error_message is not None:
            task_data.error_message = error_message
        task_data.updated_at = datetime.utcnow()
        
        # Save to Redis
        await redis_client.hset(f"task:{task_id}", "data", task_data.model_dump_json())
        
        # If task is completed/failed, clean up
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            await self._cleanup_completed_task(task_id, task_data.user_id)
    
    async def get_task_status(self, task_id: str) -> Optional[TaskResponse]:
        """Get current task status."""
        redis_client = await self._get_redis()
        
        task_json = await redis_client.hget(f"task:{task_id}", "data")
        if not task_json:
            return None
        
        task_data = TaskData.model_validate_json(task_json)
        return TaskResponse.model_validate(task_data.model_dump())
    
    async def get_user_active_tasks(self, user_id: str) -> List[TaskResponse]:
        """Get all active tasks for a user."""
        redis_client = await self._get_redis()
        
        task_ids = await redis_client.smembers(f"user:{user_id}:active_tasks")
        tasks = []
        
        for task_id in task_ids:
            task_data = await self.get_task_status(task_id)
            if task_data:
                tasks.append(task_data)
        
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)
    
    async def get_user_completed_tasks(self, user_id: str, limit: int = 10) -> List[TaskResponse]:
        """Get completed tasks for a user."""
        redis_client = await self._get_redis()
        
        # Get completed task IDs (we store last N completed tasks)
        task_ids = await redis_client.lrange(f"user:{user_id}:completed_tasks", 0, limit - 1)
        tasks = []
        
        for task_id in task_ids:
            task_data = await self.get_task_status(task_id)
            if task_data:
                tasks.append(task_data)
        
        return tasks
    
    async def cancel_task(self, task_id: str, user_id: str) -> bool:
        """Cancel a pending or processing task."""
        redis_client = await self._get_redis()
        
        # Check if task exists and belongs to user
        task_data = await self.get_task_status(task_id)
        if not task_data or task_data.user_id != user_id:
            return False
        
        # Can only cancel pending or processing tasks
        if task_data.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            return False
        
        # Update status to cancelled
        await self.update_task_status(task_id, TaskStatus.CANCELLED)
        return True
    
    async def _cleanup_completed_task(self, task_id: str, user_id: str):
        """Move completed task from active to completed list."""
        redis_client = await self._get_redis()
        
        pipe = redis_client.pipeline()
        pipe.srem(f"user:{user_id}:active_tasks", task_id)
        pipe.lpush(f"user:{user_id}:completed_tasks", task_id)
        pipe.ltrim(f"user:{user_id}:completed_tasks", 0, 99)  # Keep last 100 completed tasks
        pipe.decr("global:active_tasks_count")
        await pipe.execute()
    
    async def cleanup_expired_tasks(self):
        """Cleanup expired tasks (called periodically)."""
        redis_client = await self._get_redis()
        
        # This would be called by a background cleanup process
        # For now, Redis TTL handles cleanup automatically
        pass


task_manager = TaskManagerService()