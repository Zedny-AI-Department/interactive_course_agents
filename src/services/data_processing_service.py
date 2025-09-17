from typing import List
from fastapi import UploadFile
import string

from src.services.file_processing_service import FileProcessingService
from src.services.image_service import ImageProcessingService
from src.services import VideoService, SRTService, LLMService
from src.models import (
    GeneratedParagraphWithVisualListModel,
    ParagraphWithVisualListModel,
    ParagraphWithVisualModel,
    GeneratedVisualItemModel,
    VisualItemModel,
    WordTranscriptionModel,
    ParagraphItem,
    ParagraphsAlignmentWithVideoResponse,
    GeneratedParagraphsVisualAlignmentModel,
    SearchedImageVisualModel,
    VisualMappingModel,
    GeneratedParagraphWithVisualModel
    
)
from src.constants import ParagraphAlignmentWithVisualPrompt, ParagraphWithVisualPrompt


class DataProcessingService:
    """A service that handles interactions with data processing tools."""

    def __init__(
        self,
        video_service: VideoService,
        srt_service: SRTService,
        llm_service: LLMService,
        img_service: ImageProcessingService,
        file_processing_service: FileProcessingService,
    ):
        self.video_service = video_service
        self.srt_service = srt_service
        self.llm_service = llm_service
        self.img_service = img_service
        self.file_processing_service = file_processing_service

    async def generate_paragraphs_with_visuals(
        self, srt_file: UploadFile, media_file: UploadFile
    ) -> ParagraphWithVisualListModel:
        """Process the SRT file and media file to produce aligned output."""
        # Extract text from SRT file
        srt_text = await self.srt_service.extract_text(srt_file=srt_file)
        # Generate paragraphs with metadata using LLM service
        formatted_prompt = self.llm_service.format_prompt(
            system_message=ParagraphWithVisualPrompt.SYSTEM_PROMPT,
            user_message=ParagraphWithVisualPrompt.USER_PROMPT,
            script=srt_text,
            output_schema=GeneratedParagraphWithVisualListModel.model_json_schema(),
        )
        generated_output: GeneratedParagraphWithVisualListModel = (
            await self.llm_service.ask_search_agent(
                model_name="gpt-4o",
                model_provider="openai",
                output_schema=GeneratedParagraphWithVisualListModel,
                prompt=formatted_prompt,
            )
        )
        # Align generated paragraphs with video and extract word timestamps
        paragraphs = [
            ParagraphItem(
                text=paragraph.paragraph_text, paragraph_index=paragraph.paragraph_index
            )
            for paragraph in generated_output.paragraphs
        ]
        video_paragraph_alignment_result = (
            await self.video_service.align_paragraph_with_media(
                media_file=media_file, paragraphs=paragraphs
            )
        )
        combined_result = self._merge_video_alignment_with_generated_paragraphs(
            video_paragraph_alignment_result=video_paragraph_alignment_result,
            generated_output=generated_output,
        )
        return ParagraphWithVisualListModel(paragraphs=combined_result)

    async def extract_and_align_pdf_visuals(
        self, srt_file: UploadFile, media_file: UploadFile, pdf_file: UploadFile
    ) -> ParagraphWithVisualListModel:
        """Process the SRT file and media file to produce aligned output."""
        # Extract text from SRT file
        srt_text = await self.srt_service.extract_text(srt_file=srt_file)
        # Extract and process images
        pdf_bytes = await pdf_file.read()
        extracted_visuals = self.file_processing_service.extract_images_from_pdf(
            pdf_bytes=pdf_bytes
        )
        processed_visuals: List[SearchedImageVisualModel] = (
            await self.img_service.search_images(original_images=extracted_visuals)
        )
        
        # Generate paragraphs with metadata using LLM service
        visuals_map = [
            VisualMappingModel(
                visual_index=visual.visual_index, visual_description=visual.description
            )
            for visual in processed_visuals
        ]
        formatted_prompt = self.llm_service.format_prompt(
            system_message=ParagraphAlignmentWithVisualPrompt.SYSTEM_PROMPT,
            user_message=ParagraphAlignmentWithVisualPrompt.USER_PROMPT,
            script=srt_text,
            provided_visuals=visuals_map,
            output_schema=GeneratedParagraphsVisualAlignmentModel.model_json_schema(),
        )
        generated_output: GeneratedParagraphsVisualAlignmentModel = (
            await self.llm_service.ask_openai_llm(
                model_name="gpt-4o",
                model_provider="openai",
                output_schema=GeneratedParagraphsVisualAlignmentModel,
                prompt=formatted_prompt,
            )
        )
        print(f"generated_output: {generated_output}")

        # Aligned paragraphs with extracted visuals
        aligned_paragraphs = self._match_paragraphs_to_extracted_visuals(generated_output=generated_output, processed_visuals=processed_visuals)
        # Align generated paragraphs with video and extract word timestamps
        paragraphs = [
            ParagraphItem(
                text=paragraph.paragraph_text, paragraph_index=paragraph.paragraph_index
            )
            for paragraph in aligned_paragraphs
        ]
        video_paragraph_alignment_result = (
            await self.video_service.align_paragraph_with_media(
                media_file=media_file, paragraphs=paragraphs
            )
        )
        combined_result = self._merge_video_alignment_with_generated_paragraphs(
            video_paragraph_alignment_result=video_paragraph_alignment_result,
            generated_output=generated_output,
            external_visuals=processed_visuals,
        )
        return ParagraphWithVisualListModel(paragraphs=combined_result)

    def _merge_video_alignment_with_generated_paragraphs(
        self,
        video_paragraph_alignment_result: ParagraphsAlignmentWithVideoResponse,
        generated_output: GeneratedParagraphWithVisualListModel,
    ) -> List[ParagraphWithVisualModel]:
        """Combine the results from the transcript and aligned output."""
        combined_result = []
        if len(video_paragraph_alignment_result.result) != len(
            generated_output.paragraphs
        ):
            raise Exception(
                "Generated paragraphs and aligned paragraphs must be matched in length."
            )

        for paragraph in generated_output.paragraphs:
            # Get aligned paragraph
            aligned_paragraph = next(
                (
                    aligned_paragraph
                    for aligned_paragraph in video_paragraph_alignment_result.result
                    if aligned_paragraph.paragraph_index == paragraph.paragraph_index
                ),
                None,
            )

            # Prepare visual data
            if paragraph.visuals is not None:
                print(f"{paragraph.paragraph_index}: {paragraph.visuals.model_dump()}")
                processed_visual_model = self._map_visual_to_word_timestamps(
                    visual_model=paragraph.visuals,
                    paragraph_words=aligned_paragraph.paragraph_words,
                )
            else:
                processed_visual_model = None

            processed_paragraph = ParagraphWithVisualModel(
                paragraph_id=paragraph.paragraph_index + 1,
                paragraph_text=paragraph.paragraph_text,
                start_time=aligned_paragraph.start,
                end_time=aligned_paragraph.end,
                keywords=[keyword.model_dump() for keyword in paragraph.keywords],
                words=[
                    {"word": word.text, "start": word.start, "end": word.end}
                    for word in aligned_paragraph.paragraph_words
                ],
                visuals=(
                    processed_visual_model.model_dump()
                    if processed_visual_model
                    else None
                ),
            )
            combined_result.append(processed_paragraph)
        return combined_result

    def _map_visual_to_word_timestamps(
        self,
        visual_model: GeneratedVisualItemModel,
        paragraph_words: List[WordTranscriptionModel],
    ) -> VisualItemModel:
        """Prepare the visual model for use in the service."""
        visual_start_words = self._clean_text(visual_model.start_sentence).split(" ")
        visual_start_words = [word.strip() for word in visual_start_words]
        for index in range(len(paragraph_words) - len(visual_start_words) + 1):
            seq_words = [
                self._clean_text(word.text).strip()
                for word in paragraph_words[index : index + len(visual_start_words)]
            ]
            if visual_start_words == seq_words:
                processed_visual_model = VisualItemModel(
                    type=visual_model.type,
                    content=visual_model.content.model_dump(),
                    start_time=paragraph_words[index].start,
                )
                return processed_visual_model
        return None

    def _match_paragraphs_to_extracted_visuals(
        self,
        generated_output: GeneratedParagraphsVisualAlignmentModel,
        processed_visuals: List[SearchedImageVisualModel],
    ) -> List[GeneratedParagraphWithVisualModel]:
        aligned_result = []
        for paragraph in generated_output.paragraphs:
            # Get aligned visual data
            if paragraph.visuals is not None:
                print(f"{paragraph.paragraph_index}: {paragraph.visuals.model_dump()}")
                aligned_visual = next(
                    (
                        aligned_visual
                        for aligned_visual in processed_visuals
                        if aligned_visual.visual_index == paragraph.visuals.visual_index
                    ),
                    None,
                )
                paragraph.visuals = None
                aligned_paragraph = GeneratedParagraphWithVisualModel.model_validate(paragraph)
                aligned_paragraph.visuals = aligned_visual
                aligned_result.append(aligned_paragraph)
        return aligned_result

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean the text by removing punctuation and converting to lowercase."""
        table = str.maketrans("", "", string.punctuation)
        clean_text = text.translate(table)
        return clean_text.lower()
