from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends, BackgroundTasks
from typing import Optional, Dict, Any
import tempfile
import os
import httpx

from src.services.image_service import ImageProcessingService
from src.services.llm_service import LLMService
from src.services import auth_service, task_manager
from src.services.background_processor import background_processor
from src.models.task_models import CreateTaskResponse

image_processing_router = APIRouter(prefix="/image", tags=["image"])


def get_image_processing_service():
    """Dependency to get image processing service instance."""
    llm_service = LLMService()
    return ImageProcessingService(llm_service)


@image_processing_router.post("/convert-to-3d/file")
async def convert_image_to_3d(
    image_file: UploadFile = File(..., description="Image file to convert to 3D"),
    geometry_format: str = Form(default="glb", description="Output geometry format"),
    quality: str = Form(
        default="medium", description="Quality setting (low, medium, high)"
    ),
    service: ImageProcessingService = Depends(get_image_processing_service),
) -> Dict[str, Any]:
    """Convert an uploaded image to a 3D model.

    Args:
        image_file: The image file to convert
        geometry_format: Output format (default: "glb")
        quality: Quality setting (default: "medium")
        service: Image processing service instance

    Returns:
        Dict containing the 3D conversion result
    """
    try:
        # Validate file type
        if not image_file.content_type or not image_file.content_type.startswith(
            "image/"
        ):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Create temporary file for the uploaded image
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(image_file.filename or "image.jpg")[1]
        ) as tmp_file:
            content = await image_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # Convert image to 3D
            result = await service.convert_image_to_3d(
                image_path=tmp_file_path,
                geometry_format=geometry_format,
                quality=quality,
            )

            return {
                "success": True,
                "message": "Image successfully converted to 3D",
                "result": result,
                "input_filename": image_file.filename,
                "geometry_format": geometry_format,
                "quality": quality,
            }

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while converting image to 3D: {str(e)}",
        )


@image_processing_router.post("/convert-to-3d/url")
async def convert_image_to_3d_from_url(
    image_url: str = Form(..., description="URL of the image to convert to 3D"),
    geometry_format: str = Form(default="glb", description="Output geometry format"),
    quality: str = Form(
        default="medium", description="Quality setting (low, medium, high)"
    ),
    user_id: str = Depends(auth_service.get_current_user_id),
    service: ImageProcessingService = Depends(get_image_processing_service),
) -> Dict[str, Any]:
    """Convert an image from URL to a 3D model.

    Args:
        image_url: URL of the image to convert
        geometry_format: Output format (default: "glb")
        quality: Quality setting (default: "medium")
        user_id: Current user ID from auth
        service: Image processing service instance

    Returns:
        Dict containing the 3D conversion result
    """
    try:
        # Download image from URL
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_content = response.content
            
            # Determine file extension from content-type or URL
            content_type = response.headers.get('content-type', '')
            if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                file_extension = '.jpg'
            elif 'image/png' in content_type:
                file_extension = '.png'
            elif 'image/webp' in content_type:
                file_extension = '.webp'
            else:
                # Fallback to URL extension or default to .jpg
                file_extension = os.path.splitext(image_url)[1] or '.jpg'
        
        # Create temporary file for the downloaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(image_content)
            tmp_file_path = tmp_file.name

        try:
            # Convert image to 3D using local file path
            result = await service.convert_image_to_3d(
                image_path=tmp_file_path, geometry_format=geometry_format, quality=quality
            )

            return {
                "success": True,
                "message": "Image successfully converted to 3D",
                "result": result,
                "input_url": image_url,
                "geometry_format": geometry_format,
                "quality": quality,
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while converting image to 3D: {str(e)}",
        )


@image_processing_router.post("/convert-to-3d/file/async", response_model=CreateTaskResponse)
async def convert_image_to_3d_async(
    background_tasks: BackgroundTasks,
    image_file: UploadFile = File(..., description="Image file to convert to 3D"),
    geometry_format: str = Form(default="glb", description="Output geometry format"),
    quality: str = Form(
        default="medium", description="Quality setting (low, medium, high)"
    ),
    user_id: str = Depends(auth_service.get_current_user_id),
):
    """Create a background task to convert an image to 3D model.
    
    Args:
        background_tasks: FastAPI background tasks manager
        image_file: The image file to convert
        geometry_format: Output format (default: "glb")
        quality: Quality setting (default: "medium")
        user_id: Current user ID from auth
        
    Returns:
        CreateTaskResponse with task_id for tracking progress
    """
    try:
        # Validate file type
        if not image_file.content_type or not image_file.content_type.startswith(
            "image/"
        ):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Create task
        task_id = await task_manager.create_task(user_id, "convert_image_to_3d")
        
        # Read file content
        image_content = await image_file.read()
        
        # Add background task
        background_tasks.add_task(
            background_processor.convert_image_to_3d_task,
            task_id,
            image_content,
            image_file.filename,
            geometry_format,
            quality
        )
        
        return CreateTaskResponse(
            task_id=task_id,
            status="pending",
            message="3D conversion task created successfully. Use the task_id to track progress."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the 3D conversion task: {str(e)}",
        )


@image_processing_router.post("/convert-to-3d-from/url/async", response_model=CreateTaskResponse)
async def convert_image_url_to_3d_async(
    background_tasks: BackgroundTasks,
    image_url: str = Form(..., description="URL of the image to convert to 3D"),
    geometry_format: str = Form(default="glb", description="Output geometry format"),
    quality: str = Form(
        default="medium", description="Quality setting (low, medium, high)"
    ),
    user_id: str = Depends(auth_service.get_current_user_id),
):
    """Create a background task to convert an image from URL to 3D model.
    
    Args:
        background_tasks: FastAPI background tasks manager
        image_url: URL of the image to convert
        geometry_format: Output format (default: "glb")
        quality: Quality setting (default: "medium")
        user_id: Current user ID from auth
        
    Returns:
        CreateTaskResponse with task_id for tracking progress
    """
    try:
        # Create task
        task_id = await task_manager.create_task(user_id, "convert_image_url_to_3d")
        
        # Add background task
        background_tasks.add_task(
            background_processor.convert_image_url_to_3d_task,
            task_id,
            image_url,
            geometry_format,
            quality
        )
        
        return CreateTaskResponse(
            task_id=task_id,
            status="pending",
            message="3D conversion task from URL created successfully. Use the task_id to track progress."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the 3D conversion task from URL: {str(e)}",
        )
