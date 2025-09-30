from src.clients import InteractiveDBClient
from src.models.interactive_db_models import (
    FileResponseSchema,
    GetTypesResponseSchema,
    ImageCreateSchema,
    ImageResponseSchema,
)


class InteractiveDBRepository:
    def __init__(self, interactive_db_client: InteractiveDBClient):
        self.interactive_db_client = interactive_db_client

    # Get routes methods
    async def get_file_types(self) -> GetTypesResponseSchema:
        """Get file types from API endpoint."""
        api_result = await self.interactive_db_client.get_file_types() 
        return GetTypesResponseSchema(**api_result)

    async def get_word_types(self) -> GetTypesResponseSchema:
        """Get word types from API endpoint."""
        api_result = await self.interactive_db_client.get_word_types()
        return GetTypesResponseSchema(**api_result)

    async def get_keyword_types(self) -> GetTypesResponseSchema:
        """Get keyword types from API endpoint."""
        api_result = await self.interactive_db_client.get_keyword_types()
        return GetTypesResponseSchema(**api_result)

    async def get_visual_types(self) -> GetTypesResponseSchema:
        """Get visual types from API endpoint."""
        api_result = await self.interactive_db_client.get_visual_types()
        return GetTypesResponseSchema(**api_result)

    async def get_chart_types(self) -> GetTypesResponseSchema:
        """Get chart types from API endpoint."""
        api_result = await self.interactive_db_client.get_chart_types()
        return GetTypesResponseSchema(**api_result)

    async def save_assist_file(
        self, file_bytes: str, file_name, file_type_id: str, content_type: str
    ) -> FileResponseSchema:
        """Save assist file with its metadata to database via API."""
        try:
            assist_file_data = {"file_type_id": str(file_type_id), "video_id": None}
            assist_file_file = {"file": (file_name, file_bytes, content_type)}
            api_result = FileResponseSchema(
                **await self.interactive_db_client.save_assist_file(
                    assist_file_data=assist_file_data, assist_file_file=assist_file_file
                )
            )
            return api_result
        except Exception as e:
            raise Exception(f"Error while saving assist file: {str(e)}")

    async def save_image(
        self,
        image_data: ImageCreateSchema,
        image_bytes: bytes,
        image_name: str,
        content_type: str,
    ) -> ImageResponseSchema:
        """Save image metadata to database via API."""
        try:

            image_data_dict = image_data.model_dump()
            image_data_dict["file_id"] = str(image_data.file_id)
            image_file = {"image": (image_name, image_bytes, content_type)}
            api_result = await self.interactive_db_client.save_image(
                image_data=image_data_dict, image_file=image_file
            )
            return ImageResponseSchema(**api_result)
        except Exception as e:
            raise Exception(f"Error while saving image: {str(e)}")

    async def save_video_file(
        self, video_bytes: bytes, video_name: str, content_type: str
    ) -> str:
        """Save video metadata to database via API."""
        try:
            video_file = {"video_file": (video_name, video_bytes, content_type)}
            
            api_result = await self.interactive_db_client.save_video(video_file=video_file)
            return FileResponseSchema(**api_result)
        except Exception as e:
            raise Exception(f"Error while saving video: {str(e)}")

    async def update_image_with_3d(
        self,
        image_3d_bytes: bytes,
        image_3d_name: str,
        image_3d_content_type: str,
        assist_image_id: str,
    ) -> ImageResponseSchema:
        """save 3d image for existing image in DB."""
        try:
            image_3d_file = {
                "image_3d": (image_3d_name, image_3d_bytes, image_3d_content_type)
            }
            api_result = ImageResponseSchema(
                **await self.interactive_db_client.save_image_with_3d(
                    image_3d_file=image_3d_file, assist_image_id=assist_image_id
                )
            )
            return api_result.image_3d_url

        except Exception as e:
            raise Exception(f"Error while saving 3d image: {str(e)}")
