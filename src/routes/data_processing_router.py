from fastapi import (
    APIRouter,
    File,
    Query,
    UploadFile,
    HTTPException,
    BackgroundTasks,
    Depends,
)

from src.services.data_processing_service import DataProcessingService
from src.services.background_processor import BackgroundProcessor
from src.container import get_data_processing_service, get_background_processor
from src.models import EducationalContent
from src.models.task_models import CreateTaskResponse, TaskResponse, UserTasksResponse, AgentMode, VideoMetadata
from src.services import task_manager, auth_service


data_processing_router = APIRouter(prefix="/content", tags=["content"])
task_router = APIRouter(prefix="/task", tags=["tasks"])

# Endpoints

# Background task endpoints

@data_processing_router.post("/process-async", response_model=CreateTaskResponse)
async def create_general_processing_task(
    background_tasks: BackgroundTasks,
    srt_file: UploadFile = File(..., description="SRT subtitle file"),
    media_file: UploadFile = File(..., description="Art/media file (video, audio, etc.)"),
    agent_mode: AgentMode = Query(..., description="Agent processing mode"),
    course_id: str = Query(..., description="Course identifier"),
    chapter_id: str = Query(..., description="Chapter identifier"),
    video_name: str = Query(..., description="Video name"),
    pdf_file: UploadFile = File(None, description="Optional PDF assistance file"),
    user_id: str = Depends(auth_service.get_current_user_id),
    background_processor: BackgroundProcessor = Depends(get_background_processor)
):
    """Create a background task for general data processing with different agent modes."""
    try:
        # Create task with course metadata
        video_metadata = VideoMetadata(
            course_id=course_id,
            chapter_id=chapter_id,
            video_name=video_name,
            agent_mode=agent_mode
        )
        task_id = await task_manager.create_task(user_id, video_metadata=video_metadata)

        # Read file contents
        srt_content = await srt_file.read()
        media_content = await media_file.read()

        # Handle different agent modes
        if agent_mode == AgentMode.GENERATE:
            # For generate mode, PDF is not required
            background_tasks.add_task(
                background_processor.generate_paragraphs_with_visuals_task,
                task_id,
                srt_content,
                srt_file.filename,
                media_content,
                media_file.filename,
                media_file.content_type,
            )
        else:
            # For search modes, PDF is required
            if not pdf_file:
                raise HTTPException(
                    status_code=400, 
                    detail="PDF file is required for search agent modes"
                )
            
            pdf_content = await pdf_file.read()
            
            if agent_mode == AgentMode.ALWAYS_SEARCH:
                background_tasks.add_task(
                    background_processor.extract_and_align_pdf_visuals_task,
                    task_id,
                    srt_content,
                    srt_file.filename,
                    media_content,
                    media_file.filename,
                    pdf_content,
                    pdf_file.filename,
                )
            elif agent_mode == AgentMode.SEARCH_FOR_COPYRIGHT:
                background_tasks.add_task(
                    background_processor.extract_and_align_pdf_visuals_with_copyright_task,
                    task_id,
                    srt_content,
                    srt_file.filename,
                    media_content,
                    media_file.filename,
                    pdf_content,
                    pdf_file.filename,
                )

        return CreateTaskResponse(
            task_id=task_id,
            status="pending",
            message="Task created successfully. Use the task_id to track progress.",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the task: {str(e)}",
        )


@data_processing_router.post("/generate-async", response_model=CreateTaskResponse)
async def create_generation_task(
    background_tasks: BackgroundTasks,
    srt_file: UploadFile = File(..., description="SRT subtitle file"),
    media_file: UploadFile = File(..., description="Video or audio media file"),
    course_id: str = Query(..., description="Course identifier"),
    chapter_id: str = Query(..., description="Chapter identifier"),
    video_name: str = Query(..., description="Video name"),
    user_id: str = Depends(auth_service.get_current_user_id),
    background_processor: BackgroundProcessor = Depends(get_background_processor)
):
    """Create a background task to generate educational content."""
    try:
        # Create task with course metadata
        video_metadata = VideoMetadata(
            course_id=course_id,
            chapter_id=chapter_id,
            video_name=video_name,
            agent_mode=AgentMode.GENERATE
        )
        task_id = await task_manager.create_task(
            user_id, "generate_paragraphs_with_visuals", video_metadata=video_metadata
        )

        # Read file contents
        srt_content = await srt_file.read()
        media_content = await media_file.read()

        # Add background task
        background_tasks.add_task(
            background_processor.generate_paragraphs_with_visuals_task,
            task_id,
            srt_content,
            srt_file.filename,
            media_content,
            media_file.filename,
            media_file.content_type,
        )

        return CreateTaskResponse(
            task_id=task_id,
            status="pending",
            message="Task created successfully. Use the task_id to track progress.",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the task: {str(e)}",
        )


@data_processing_router.post(
    "/search-async", response_model=CreateTaskResponse
)
async def create_pdf_visuals_task(
    background_tasks: BackgroundTasks,
    srt_file: UploadFile = File(..., description="SRT subtitle file"),
    media_file: UploadFile = File(..., description="Video or audio media file"),
    pdf_file: UploadFile = File(..., description="PDF file containing visual elements"),
    course_id: str = Query(..., description="Course identifier"),
    chapter_id: str = Query(..., description="Chapter identifier"),
    video_name: str = Query(..., description="Video name"),
    user_id: str = Depends(auth_service.get_current_user_id),
    background_processor: BackgroundProcessor = Depends(get_background_processor)
):
    """Create a background task to extract PDF visuals and align them."""
    try:
        # Create task with course metadata
        video_metadata = VideoMetadata(
            course_id=course_id,
            chapter_id=chapter_id,
            video_name=video_name,
            agent_mode=AgentMode.ALWAYS_SEARCH
        )
        task_id = await task_manager.create_task(
            user_id, "extract_and_align_pdf_visuals", video_metadata=video_metadata
        )

        # Read file contents
        srt_content = await srt_file.read()
        media_content = await media_file.read()
        pdf_content = await pdf_file.read()

        # Add background task
        background_tasks.add_task(
            background_processor.extract_and_align_pdf_visuals_task,
            task_id,
            srt_content,
            srt_file.filename,
            media_content,
            media_file.filename,
            pdf_content,
            pdf_file.filename,
        )

        return CreateTaskResponse(
            task_id=task_id,
            status="pending",
            message="Task created successfully. Use the task_id to track progress.",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the task: {str(e)}",
        )


@data_processing_router.post(
    "/search-with-copyright-async", response_model=CreateTaskResponse
)
async def create_pdf_visuals_copyright_task(
    background_tasks: BackgroundTasks,
    srt_file: UploadFile = File(..., description="SRT subtitle file"),
    media_file: UploadFile = File(..., description="Video or audio media file"),
    pdf_file: UploadFile = File(..., description="PDF file containing visual elements"),
    course_id: str = Query(..., description="Course identifier"),
    chapter_id: str = Query(..., description="Chapter identifier"),
    video_name: str = Query(..., description="Video name"),
    user_id: str = Depends(auth_service.get_current_user_id),
    background_processor: BackgroundProcessor = Depends(get_background_processor)
):
    """Create a background task to extract PDF visuals with copyright detection."""
    try:
        # Create task with course metadata
        video_metadata = VideoMetadata(
            course_id=course_id,
            chapter_id=chapter_id,
            video_name=video_name,
            agent_mode=AgentMode.SEARCH_FOR_COPYRIGHT
        )
        task_id = await task_manager.create_task(
            user_id, "extract_and_align_pdf_visuals_with_copyright_detection", video_metadata=video_metadata
        )

        # Read file contents
        srt_content = await srt_file.read()
        media_content = await media_file.read()
        pdf_content = await pdf_file.read()

        # Add background task
        background_tasks.add_task(
            background_processor.extract_and_align_pdf_visuals_with_copyright_task,
            task_id,
            srt_content,
            srt_file.filename,
            media_content,
            media_file.filename,
            pdf_content,
            pdf_file.filename,
        )

        return CreateTaskResponse(
            task_id=task_id,
            status="pending",
            message="Task created successfully. Use the task_id to track progress.",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the task: {str(e)}",
        )


@task_router.get("/{task_id}/status", response_model=TaskResponse)
async def get_task_status(
    task_id: str, user_id: str = Depends(auth_service.get_current_user_id)
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


@task_router.get("/{task_id}/result")
async def get_task_result(
    task_id: str, user_id: str = Depends(auth_service.get_current_user_id)
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
                detail=f"Task is not completed. Current status: {task_data.status}",
            )

        return {
            "task_id": task_id,
            "status": task_data.status,
            "result": task_data.result,
            "video_metadata": task_data.video_metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving task result: {str(e)}",
        )


@task_router.get("/user", response_model=UserTasksResponse)
async def get_user_tasks(
    user_id: str = Depends(auth_service.get_current_user_id),
    include_completed: bool = Query(default=True),
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
            total_completed=len(completed_tasks),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving user tasks: {str(e)}",
        )


@task_router.delete("/{task_id}")
async def cancel_task(
    task_id: str, user_id: str = Depends(auth_service.get_current_user_id)
):
    """Cancel a pending or processing task."""
    try:
        success = await task_manager.cancel_task(task_id, user_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Task cannot be cancelled (not found, not yours, or already completed)",
            )

        return {"message": "Task cancelled successfully", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while cancelling the task: {str(e)}",
        )


# Legacy sync endpoints (kept for backward compatibility)


@data_processing_router.post("/generate", response_model=EducationalContent)
async def generate_educational_content(
    srt_file: UploadFile = File(..., description="SRT subtitle file"),
    media_file: UploadFile = File(..., description="Video or audio media file"),
    course_id: str = Query(..., description="Course identifier"),
    chapter_id: str = Query(..., description="Chapter identifier"),
    video_name: str = Query(..., description="Video name"),
    data_processing_service: DataProcessingService = Depends(get_data_processing_service)
):
    """Synchronous processing endpoint (for backward compatibility)."""
    try:
        # Create course metadata
        video_metadata = VideoMetadata(
            course_id=course_id,
            chapter_id=chapter_id,
            video_name=video_name,
            agent_mode=AgentMode.GENERATE
        )
        
        # Align paragraphs with audio
        result = await data_processing_service.generate_paragraphs_with_visuals(
            media_file=media_file, srt_file=srt_file
        )
        
        # Add course metadata to result
        result.video_metadata = video_metadata
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )


@data_processing_router.post("/search", response_model=EducationalContent)
async def extract_pdf_visuals_and_align(
    srt_file: UploadFile = File(..., description="SRT subtitle file"),
    media_file: UploadFile = File(..., description="Video or audio media file"),
    pdf_file: UploadFile = File(..., description="PDF file containing visual elements"),
    course_id: str = Query(..., description="Course identifier"),
    chapter_id: str = Query(..., description="Chapter identifier"),
    video_name: str = Query(..., description="Video name"),
    data_processing_service: DataProcessingService = Depends(get_data_processing_service)
):
    """Synchronous processing endpoint (for backward compatibility)."""
    try:
        # Create course metadata
        video_metadata = VideoMetadata(
            course_id=course_id,
            chapter_id=chapter_id,
            video_name=video_name,
            agent_mode=AgentMode.ALWAYS_SEARCH
        )
        
        # Align paragraphs with audio
        result = await data_processing_service.extract_and_align_pdf_visuals(
            media_file=media_file, srt_file=srt_file, pdf_file=pdf_file
        )
        
        # Add course metadata to result
        result.video_metadata = video_metadata
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )


@data_processing_router.post(
    "/search-with-copyright", response_model=EducationalContent
)
async def extract_pdf_visuals_with_copyright_and_align(
    srt_file: UploadFile = File(..., description="SRT subtitle file"),
    media_file: UploadFile = File(..., description="Video or audio media file"),
    pdf_file: UploadFile = File(..., description="PDF file containing visual elements"),
    course_id: str = Query(..., description="Course identifier"),
    chapter_id: str = Query(..., description="Chapter identifier"),
    video_name: str = Query(..., description="Video name"),
    data_processing_service: DataProcessingService = Depends(get_data_processing_service)
):
    """Synchronous processing endpoint with copyright detection (for backward compatibility)."""
    try:
        # Create course metadata
        video_metadata = VideoMetadata(
            course_id=course_id,
            chapter_id=chapter_id,
            video_name=video_name,
            agent_mode=AgentMode.SEARCH_FOR_COPYRIGHT
        )
        
        # Align paragraphs with audio
        result = await data_processing_service.extract_and_align_pdf_visuals_with_copyright_detection(
            media_file=media_file, srt_file=srt_file, pdf_file=pdf_file
        )
        
        # Add course metadata to result
        result.video_metadata = video_metadata
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )
