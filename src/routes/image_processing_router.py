from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends, BackgroundTasks
from typing import Optional, Dict, Any
import tempfile
import os
import httpx

from src.services.storage_service import StorageService
from src.services.background_processor import BackgroundProcessor
from src.services.image_service import ImageProcessingService
from src.services import auth_service, task_manager
from src.models.task_models import CreateTaskResponse
from src.container import get_background_processor, get_image_service, get_storage_service
from src.constants import StorageAPIRoutes
from src.config import settings


image_processing_router = APIRouter(prefix="/image", tags=["image"])


@image_processing_router.post("/convert-to-3d/file/preview/")
async def convert_image_to_3d(
    image_file: UploadFile = File(..., description="Image file to convert to 3D"),
    geometry_format: str = Form(default="glb", description="Output geometry format"),
    quality: str = Form(
        default="medium", description="Quality setting (low, medium, high)"
    ),
    service: ImageProcessingService = Depends(get_image_service),
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

        try:
            image_bytes = await image_file.read()
            # Convert image to 3D
            result = await service.convert_image_to_3d(
                image_bytes=image_bytes,
                image_name=image_file.filename,
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
        except Exception as e:
            raise HTTPException(
            status_code=500,
            detail=f"An error occurred while converting image to 3D: {str(e)}",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while converting image to 3D: {str(e)}",
        )


@image_processing_router.post("/convert-to-3d/url/preview/")
async def convert_image_to_3d_from_url(
    image_url: str = Form(..., description="URL of the image to convert to 3D"),
    geometry_format: str = Form(default="glb", description="Output geometry format"),
    quality: str = Form(
        default="medium", description="Quality setting (low, medium, high)"
    ),
    service: ImageProcessingService = Depends(get_image_service),
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


@image_processing_router.post("/convert-to-3d/file/preview/async", response_model=CreateTaskResponse)
async def convert_image_to_3d_async(
    background_tasks: BackgroundTasks,
    image_file: UploadFile = File(..., description="Image file to convert to 3D"),
    geometry_format: str = Form(default="glb", description="Output geometry format"),
    quality: str = Form(
        default="medium", description="Quality setting (low, medium, high)"
    ),
    user_id: str = Depends(auth_service.get_current_user_id),
    background_processor: BackgroundProcessor = Depends(get_background_processor)
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


@image_processing_router.post("/convert-to-3d-from/url/preview/async", response_model=CreateTaskResponse)
async def convert_image_url_to_3d_async(
    background_tasks: BackgroundTasks,
    image_url: str = Form(..., description="URL of the image to convert to 3D"),
    geometry_format: str = Form(default="glb", description="Output geometry format"),
    quality: str = Form(
        default="medium", description="Quality setting (low, medium, high)"
    ),
    user_id: str = Depends(auth_service.get_current_user_id),
    background_processor: BackgroundProcessor = Depends(get_background_processor)
    
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


@image_processing_router.post("/convert-to-3d/submit/")
async def convert_to_3d_submit(
    image_3d_file: UploadFile = File(..., description="3D image file to submit"),
    assist_image_id: str = Form(..., description="Assist image ID from stored image"),
    service: StorageService = Depends(get_storage_service)
) -> Dict[str, Any]:
    """Submit a 3D image for an existing assist image.

    Args:
        image_3d_file: The 3D image file to submit
        assist_image_id: The ID of the existing assist image

    Returns:
        Dict containing the submission result with 3D image URL
    """
    try:
        # Validate file type
        if not image_3d_file.content_type or not image_3d_file.content_type.startswith("application/octet-stream"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read the 3D image file
        image_3d_bytes = await image_3d_file.read()

        image_3d_url = await service.update_image_with_3d_via_api(image_3d_bytes=image_3d_bytes, 
                                                            image_3d_name=image_3d_file.filename, 
                                                            image_3d_content_type=image_3d_file.content_type, 
                                                            assist_image_id=assist_image_id)
        
        # Return the response with 3D image URL
        return {
            "message": "3D image submitted successfully",
            "assist_image_id": assist_image_id,
            "image_3d_url": image_3d_url
        }
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"API call failed: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while submitting 3D image: {str(e)}"
        )
