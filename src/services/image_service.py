import base64
import mimetypes
from typing import Any, Dict, List

from src.constants import ImageDescriptionPrompt, ImageDescriptionWithCopyrightPrompt
from src.models import VisualContent, ExtractedImage, LLMVisualContent, LLMVisualContentWithCopyright
from src.services.llm_service import LLMService
from src.utils import search_with_tavily


class ImageProcessingService:
    """A service that handles image processing tools."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def search_images(
        self, original_images: List[ExtractedImage]
    ) -> List[LLMVisualContent]:
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
                output_schema=LLMVisualContent.model_json_schema(),
                additional_content=[
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    }
                ],
            )
            try:
                described_visual: LLMVisualContent = (
                    await self.llm_service.ask_openai_llm(
                        model_name="gpt-4o-mini",
                        output_schema=LLMVisualContent,
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
                    processed_img = LLMVisualContent(**described_data_json)
                else:
                    processed_img = LLMVisualContent(**described_visual.model_dump())
                processed_imgs.append(processed_img)
            except Exception as e:
                continue
        return processed_imgs

    async def search_images_with_copyright_detection(
        self, original_images: List[ExtractedImage]
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
            img.image_bytes = base64_image
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
                        described_data_json["content"]["url"] = searched_img["images"][0]
                        processed_img = LLMVisualContentWithCopyright(**described_data_json)
                    else:
                        # For unprotected images, use them as extracted from PDF
                        # Convert base64 to data URL for direct use
                        described_data_json = described_visual.model_dump()
                        described_data_json["content"]["url"] = f"data:{mime_type};base64,{base64_image}"
                        processed_img = LLMVisualContentWithCopyright(**described_data_json)
                else:
                    processed_img = LLMVisualContentWithCopyright(**described_visual.model_dump())
                processed_imgs.append(processed_img)
            except Exception as e:
                continue
        return processed_imgs
