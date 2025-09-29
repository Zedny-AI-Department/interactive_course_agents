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
            response = await client.get(
                f"{self.api_base_url}{StorageAPIRoutes.FILE_TYPES}"
            )
            response.raise_for_status()
            file_types = response.json()
            return FileTypesResponseSchema(**file_types)

    async def save_file_via_api(
        self, file_bytes: str, file_name, file_type_id: str, content_type: str
    ) -> str:
        """Save file metadata to database via API (dummy implementation)."""
        async with httpx.AsyncClient() as client:
            data = {"file_type_id": str(file_type_id), "video_id": None}
            files = {"file": (file_name, file_bytes, content_type)}

            response = await client.post(
                f"{self.api_base_url}{StorageAPIRoutes.FILES}", data=data, files=files
            )
            response.raise_for_status()
            result = response.json()
            return str(result["id"])

    async def save_image_via_api(
        self,
        image_data: ImageCreateSchema,
        image_bytes: bytes,
        image_name: str,
        content_type: str,
    ) -> ImageResponseSchema:
        """Save image metadata to database via API (dummy implementation)."""
        async with httpx.AsyncClient() as client:
            data = {
                "file_id": str(image_data.file_id),
                "image_title": image_data.image_title,
                "proposed_image_type": image_data.proposed_image_type.value,
                "is_protected": image_data.is_protected,
                "searched_image_url": image_data.searched_image_url,
                "image_3d_url": image_data.image_3d_url,
                "description": image_data.description,
            }
            files = {"image": (image_name, image_bytes, content_type)}
            response = await client.post(
                f"{self.api_base_url}{StorageAPIRoutes.IMAGES}", data=data, files=files
            )
            response.raise_for_status()
            return ImageResponseSchema(**response.json())

    async def update_image_with_3d_via_api(
        self,
        image_3d_bytes: bytes,
        image_3d_name: str,
        image_3d_content_type: str,
        assist_image_id: str,
    ) -> ImageResponseSchema:
        """Submit 3d image for existing image in DB."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(write=60.0, connect=10.0, read=60.0, pool=30.0)) as client:
            files = {"image_3d": (image_3d_name, image_3d_bytes, "application/octet-stream")}
            route = StorageAPIRoutes.IMAGE_3D.format(image_id=str(assist_image_id))
            try:
                response = await client.post(f"{self.api_base_url}{route}", files=files)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                print(f"❌ Request failed: {exc.response.status_code}")
                print(f"Response text: {exc.response.text}")
                raise
            except httpx.RequestError as exc:
                print(f"❌ An error occurred while requesting {exc.request.url!r}: {str(exc)}")
                print(f"❌ Request error type: {type(exc)}")
                print(f"❌ Details: {repr(exc)}")
                raise

            result = ImageResponseSchema(**response.json())
            return result.image_3d_url


    async def save_video_via_api(
        self,
        video_bytes: bytes,
        video_name: str,
        content_type: str,
    ) -> ImageResponseSchema:
        """Save image metadata to database via API (dummy implementation)."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(write=500.0, connect=60.0, read=500.0, pool=300.0)) as client:
            files = {"video_file": (video_name, video_bytes, content_type)}
            response = await client.post(
                f"{self.api_base_url}{StorageAPIRoutes.VIDEO}", files=files
            )
            response.raise_for_status()
            return str(response.json()["results"]["file_id"])
