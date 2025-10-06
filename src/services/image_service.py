import base64
import mimetypes
import tempfile
from typing import Any, Dict, List
import fal_client
import os

from src.models.visual_content_models import LLMVisualContentWithCopyrightWithBytes
from src.repositories.interactive_db_repository import InteractiveDBRepository
from src.constants import ImageDescriptionPrompt, ImageDescriptionWithCopyrightPrompt
from src.models import (
    ExtractedImage,
    LLMsearchedVisualContent,
    LLMVisualContentWithCopyright,
)
from src.services.llm_service import LLMService
from src.utils import search_with_tavily
from src.config import settings


class ImageProcessingService:
    """A service that handles image processing tools."""

    def __init__(self, llm_service: LLMService, interactive_db_repository: InteractiveDBRepository):
        self.llm_service = llm_service
        self.interactive_db_repository = interactive_db_repository

    async def search_images(
        self, original_images: List[ExtractedImage], file_description: str = ""
    ) -> List[LLMsearchedVisualContent]:
        processed_imgs = []
        for index, img in enumerate(original_images):
            # Decode image
            mime_type = mimetypes.guess_type("file.png")[0] or "image/jpeg"
            base64_image = base64.b64encode(img.image_bytes).decode("utf-8")
            img.image_bytes = base64_image
            # Format prompt
            formatted_prompt = self.llm_service.format_prompt(
                system_message=ImageDescriptionPrompt.SYSTEM_PROMPT,
                user_message=ImageDescriptionPrompt.USER_PROMPT,
                output_schema=LLMsearchedVisualContent.model_json_schema(),
                additional_content=[
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    }
                ],
                general_topic=file_description,
            )
            try:
                described_visual: LLMsearchedVisualContent = (
                    await self.llm_service.ask_openai_llm(
                        model_name="gpt-4o-mini",
                        output_schema=LLMsearchedVisualContent,
                        prompt=formatted_prompt,
                    )
                )
                described_visual.visual_index = img.image_index
                if described_visual.type.lower().strip() == "image":
                    searched_img = await search_with_tavily(
                        query=described_visual.description
                    )
                    described_data_json = described_visual.model_dump()
                    described_data_json["content"]["url"] = searched_img["images"][0]
                    processed_img = LLMsearchedVisualContent(**described_data_json)
                else:
                    processed_img = LLMsearchedVisualContent(
                        **described_visual.model_dump()
                    )
                processed_imgs.append(processed_img)
            except Exception as e:
                continue
        return processed_imgs

    async def search_images_with_copyright_detection(
        self, original_images: List[ExtractedImage], file_description = ""
    ) -> List[LLMVisualContentWithCopyright]:
        """Process images with copyright assessment.

        For protected images, only search for them. For unprotected images,
        use them as extracted from PDF.

        Args:
            original_images: List of extracted images to process

        Returns:
            List of processed visuals with copyright information
        """
        processed_imgs = []
        for index, img in enumerate(original_images):
            # Decode image
            mime_type = mimetypes.guess_type("file.png")[0] or "image/jpeg"
            base64_image = base64.b64encode(img.image_bytes).decode("utf-8")            
            # Format prompt for copyright detection
            formatted_prompt = self.llm_service.format_prompt(
                system_message=ImageDescriptionWithCopyrightPrompt.SYSTEM_PROMPT,
                user_message=ImageDescriptionWithCopyrightPrompt.USER_PROMPT,
                output_schema=LLMVisualContentWithCopyright.model_json_schema(),
                additional_content=[
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    }
                ],
                general_topic=file_description
            )
            try:
                described_visual: LLMVisualContentWithCopyright = (
                    await self.llm_service.ask_openai_llm(
                        model_name="gpt-4o-mini",
                        output_schema=LLMVisualContentWithCopyright,
                        prompt=formatted_prompt,
                    )
                )
                described_visual.visual_index = img.image_index

                # Handle protected vs unprotected images
                if described_visual.type.lower().strip() == "image":
                    if described_visual.is_protected:
                        # For protected images, search for similar ones
                        searched_img = await search_with_tavily(
                            query=described_visual.description
                        )
                        described_data_json = described_visual.model_dump()
                        described_data_json["content"]["url"] = searched_img["images"][
                            0
                        ]
                        processed_img = LLMVisualContentWithCopyright(
                            **described_data_json
                        )
                    else:
                        # For unprotected images, use them as extracted from PDF
                        # Convert base64 to data URL for direct use
                        described_data_json = described_visual.model_dump()
                        described_data_json["content"][
                            "url"
                        ] = f"data:{mime_type};base64,{base64_image}"
                        processed_img = LLMVisualContentWithCopyright(
                            **described_data_json
                        )
                else:
                    processed_img = LLMVisualContentWithCopyright(
                        **described_visual.model_dump()
                    )
                processed_img_with_bytes = LLMVisualContentWithCopyrightWithBytes(**processed_img.model_dump(), image_bytes=img.image_bytes)
                processed_imgs.append(processed_img_with_bytes)
            except Exception as e:
                print(f"Error processing image {index + 1}: {str(e)}")
        return processed_imgs

    async def convert_image_to_3d(
        self,
        image_bytes: bytes,
        image_name: str,
        geometry_format: str = "glb",
        quality: str = "medium",
    ) -> Dict[str, Any]:
        """Convert image to 3D model using fal-ai/hyper3d/rodin.

        Args:
            image_bytes: bytes of the input image file
            geometry_format: Output geometry format (default: "glb")
            material: Material type (default: "PBR")
            quality: Quality setting (default: "medium")

        Returns:
            Dict containing the 3D conversion result
        """
        # Create temporary file for the uploaded image
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(image_name or "image.jpg")[1]
        ) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_file_path = tmp_file.name
        try:
            os.environ["FAL_KEY"] = settings.FAL_KEY
            # Encode image as data URL for fal_client
            image_data_url = fal_client.encode_file(tmp_file_path)
            input_args = {
                "input_image_urls": [image_data_url],
                "geometry_file_format": geometry_format,
                "quality": quality,
            }
            result = fal_client.subscribe(
                "fal-ai/hyper3d/rodin",
                arguments=input_args,
            )
            return result["model_mesh"]
        except Exception as e:
            raise Exception(f"Failed to convert image to 3D: {str(e)}")

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    async def submit_3d_image(
        self,
        image_3d_bytes: bytes,
        image_3d_name: str,
        image_3d_content_type: str,
        assist_image_id: str,
    ) -> str:
        result =  await self.interactive_db_repository.update_image_with_3d(
            image_3d_bytes=image_3d_bytes,
            image_3d_name=image_3d_name,
            image_3d_content_type=image_3d_content_type,
            assist_image_id=assist_image_id,
        )
        return result.image_3d_url
