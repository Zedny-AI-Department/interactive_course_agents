import uuid
from typing import Dict
import httpx
from src.models.storage_models import (
    FileCreateSchema,
    FileTypesResponseSchema, 
    ImageCreateSchema, 
    ImageResponseSchema,
)
from src.config import settings
from src.constants import StorageAPIRoutes


class StorageService:
    """Service for handling PDF file and extracted image storage with dummy API endpoints."""
    
    def __init__(self):
        # API base URL from environment
        self.api_base_url = settings.STORAGE_API_URL
    
    async def get_file_types(self) -> FileTypesResponseSchema:
        """Get file types from API endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base_url}{StorageAPIRoutes.FILE_TYPES}")
            response.raise_for_status()
            file_types = response.json()
            return FileTypesResponseSchema(**file_types)
        
    async def save_file_via_api(self, file_bytes: str, file_name, file_type_id: str, content_type: str) -> str:
        """Save file metadata to database via API (dummy implementation)."""
        async with httpx.AsyncClient() as client:
            data = {"file_type_id": str(file_type_id), "video_id": None}
            files = {
                "file": (file_name, file_bytes, content_type)  
            }

            response = await client.post(
                f"{self.api_base_url}{StorageAPIRoutes.FILES}",
                data=data, files=files
            )
            response.raise_for_status()
            result = response.json()
            return str(result["id"])
            
    async def save_image_via_api(self, image_data: ImageCreateSchema, image_bytes: bytes, image_name: str, content_type: str) -> ImageResponseSchema:
        """Save image metadata to database via API (dummy implementation)."""
        async with httpx.AsyncClient() as client:
            data = {
                "file_id": str(image_data.file_id),
                "image_title": image_data.image_title,
                "proposed_image_type": image_data.proposed_image_type.value,
                "is_protected": image_data.is_protected,
                "searched_image_url": image_data.searched_image_url,
                "image_3d_url": image_data.image_3d_url,
                "description": image_data.description
            }
            print("-------------------")
            print(data)
            files = {
                "image": (image_name, image_bytes, content_type)  
            }
            response = await client.post(
                f"{self.api_base_url}{StorageAPIRoutes.IMAGES}",
                data=data,
                files=files
            )
            response.raise_for_status()
            return ImageResponseSchema(**response.json())
        