from typing import Any, Dict

import httpx

from src.constants import StorageAPIRoutes


class InteractiveDBClient:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    async def get_file_types(self) -> Dict[str, Any]:
        """Get file types from API endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}{StorageAPIRoutes.GET_FILE_TYPES}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Error while getting file types: {str(e)}")

    async def get_word_types(self) -> Dict[str, Any]:
        """Get word types from API endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}{StorageAPIRoutes.GET_WORD_TYPES}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Error while getting word types: {str(e)}")

    async def get_keyword_types(self) -> Dict[str, Any]:
        """Get keyword types from API endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}{StorageAPIRoutes.GET_KEYWORD_TYPES}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Error while getting keyword types: {str(e)}")

    async def get_visual_types(self) -> Dict[str, Any]:
        """Get visual types from API endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}{StorageAPIRoutes.GET_VISUAL_TYPES}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Error while getting visual types: {str(e)}")

    async def get_chart_types(self) -> Dict[str, Any]:
        """Get chart types from API endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}{StorageAPIRoutes.GET_CHART_TYPES}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Error while getting chart types: {str(e)}")

    async def save_assist_file(
        self, assist_file_data: Dict, assist_file_file: Dict
    ) -> Dict[str, Any]:
        """Save assist file with its metadata to database via API."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(write=60.0, connect=10.0, read=60.0, pool=30.0)) as client:
                response = await client.post(
                    f"{self.api_base_url}{StorageAPIRoutes.CREATE_ASSIST_FILE}",
                    data=assist_file_data,
                    files=assist_file_file,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Error while saving assist file: {str(e)}")

    async def save_image(self, image_data: Dict, image_file: Dict) -> Dict[str, Any]:
        """Save image metadata to database via API."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(write=60.0, connect=10.0, read=60.0, pool=30.0)) as client:
                response = await client.post(
                    f"{self.api_base_url}{StorageAPIRoutes.CREATE_IMAGES}",
                    data=image_data,
                    files=image_file,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Error while saving image: {str(e)}")
        
    async def save_video(
        self,
        video_file: Dict
    ) -> Dict[str, Any]:
        """Save video metadata to database via API."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(write=500.0, connect=60.0, read=500.0, pool=300.0)) as client:
                response = await client.post(
                    f"{self.api_base_url}{StorageAPIRoutes.UPLOAD_VIDEO}", files=video_file
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise Exception(f"Error while saving video: {str(e)}")
        
    async def save_image_with_3d(
        self,
        image_3d_file: Dict,
        assist_image_id: str,
    ) -> Dict[str, Any]:
        """save 3d image for existing image in DB."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(write=60.0, connect=10.0, read=60.0, pool=30.0)) as client:
                route = StorageAPIRoutes.CREATE_IMAGE_3D.format(image_id=str(assist_image_id))
                response = await client.post(f"{self.api_base_url}{route}", files=image_3d_file)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as exc:
            raise Exception(f"An error occurred while requesting {exc.request.url!r}: {str(exc)}")
        except httpx.HTTPStatusError as exc:
            raise Exception(f"❌ Request failed with status code: {str(exc.response.status_code)}, Error: {str(exc.response.content)}")
        except Exception as e:
            raise Exception(f"Error while saving 3d image: {str(e)}")