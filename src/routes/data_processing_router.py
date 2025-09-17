from fastapi import APIRouter, File, Query, UploadFile, HTTPException, BackgroundTasks, Depends

from src.models import ParagraphWithVisualListModel
from src.models.task_models import CreateTaskResponse, TaskResponse, UserTasksResponse
from src.services import DataProcessingService, VideoService, LLMService, SRTService, task_manager, auth_service, background_processor

data_processing_router = APIRouter()


# Pipeline
def build_pipeline():
    # Your pipeline building logic here
    video_service = VideoService()
    llm_service = LLMService()
    srt_service = SRTService()
    data_processing_service = DataProcessingService(
        video_service=video_service,
        llm_service=llm_service,
        srt_service=srt_service,
    )
    return data_processing_service

# Endpoints

# Background task endpoints

@data_processing_router.post("/process/srt_media/",
                             response_model=CreateTaskResponse)
async def create_processing_task(
    background_tasks: BackgroundTasks,
    srt_file: UploadFile = File(...),
    media_file: UploadFile = File(...),
    user_id: str = Depends(auth_service.get_current_user_id)
):
    """Create a background task to process SRT and media files."""
    try:
        # Create task
        task_id = await task_manager.create_task(user_id, "process_srt_media")
        
        # Read file contents
        srt_content = await srt_file.read()
        media_content = await media_file.read()
        
        # Add background task
        background_tasks.add_task(
            background_processor.process_srt_media_task,
            task_id,
            srt_content,
            srt_file.filename,
            media_content,
            media_file.filename,
            media_file.content_type
        )
        
        return CreateTaskResponse(
            task_id=task_id,
            status="pending",
            message="Task created successfully. Use the task_id to track progress."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the task: {str(e)}",
        )


@data_processing_router.get("/tasks/{task_id}/status",
                           response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    user_id: str = Depends(auth_service.get_current_user_id)
):
    """Get the status of a specific task."""
    try:
        task_data = await task_manager.get_task_status(task_id)
        
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Verify task belongs to user
        if task_data.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return task_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving task status: {str(e)}",
        )


@data_processing_router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    user_id: str = Depends(auth_service.get_current_user_id)
):
    """Get the result of a completed task."""
    try:
        task_data = await task_manager.get_task_status(task_id)
        
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Verify task belongs to user
        if task_data.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if task is completed
        if task_data.status != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Task is not completed. Current status: {task_data.status}"
            )
        
        return {
            "task_id": task_id,
            "status": task_data.status,
            "result": task_data.result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving task result: {str(e)}",
        )


@data_processing_router.get("/users/me/tasks",
                           response_model=UserTasksResponse)
async def get_user_tasks(
    user_id: str = Depends(auth_service.get_current_user_id),
    include_completed: bool = Query(default=True)
):
    """Get all tasks for the current user."""
    try:
        active_tasks = await task_manager.get_user_active_tasks(user_id)
        completed_tasks = []
        
        if include_completed:
            completed_tasks = await task_manager.get_user_completed_tasks(user_id)
        
        return UserTasksResponse(
            user_id=user_id,
            active_tasks=active_tasks,
            completed_tasks=completed_tasks,
            total_active=len(active_tasks),
            total_completed=len(completed_tasks)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving user tasks: {str(e)}",
        )


@data_processing_router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    user_id: str = Depends(auth_service.get_current_user_id)
):
    """Cancel a pending or processing task."""
    try:
        success = await task_manager.cancel_task(task_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Task cannot be cancelled (not found, not yours, or already completed)"
            )
        
        return {"message": "Task cancelled successfully", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while cancelling the task: {str(e)}",
        )


# Legacy sync endpoint (kept for backward compatibility)
@data_processing_router.post("/process/srt_media/sync",
                             response_model=ParagraphWithVisualListModel)
async def process_data_sync(
    srt_file: UploadFile = File(...),
    media_file: UploadFile = File(...),
):
    """Synchronous processing endpoint (for backward compatibility)."""
    try:
        # Create pipeline
        service = build_pipeline()
        # Align paragraphs with audio
        result = await service.process_srt_file(media_file=media_file, srt_file=srt_file)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )
