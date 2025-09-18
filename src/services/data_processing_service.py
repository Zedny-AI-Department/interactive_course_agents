from typing import List
from fastapi import UploadFile
import string

from src.services.file_processing_service import FileProcessingService
from src.services.image_service import ImageProcessingService
from src.services import VideoService, SRTService, LLMService
from src.models import (
    LLMParagraphList,
    EducationalContent,
    ProcessedParagraph,
    LLMVisualItem,
    VisualContent,
    WordTranscription,
    ParagraphItem,
    MediaAlignmentResult,
    LLMVisualAlignmentResult,
    VisualMapping,
    LLMParagraphWithVisual,
    WordTimestamp,
    LLMVisualContent,
    LLMParagraphWithVisualRef,
    AlignedParagraph,
)
from src.constants import ParagraphAlignmentWithVisualPrompt, ParagraphWithVisualPrompt


class DataProcessingService:
    """Service for processing multimedia content and aligning it with visual elements.

    This service handles the complete workflow of:
    - Extracting text from SRT subtitle files
    - Generating structured paragraphs with visual metadata
    - Aligning paragraphs with video/audio timestamps
    - Processing and extracting visuals from PDF files
    - Mapping visuals to specific word timestamps

    Attributes:
        video_service: Service for video/audio processing and alignment
        srt_service: Service for SRT subtitle file processing
        llm_service: Service for Large Language Model interactions
        img_service: Service for image processing and search
        file_processing_service: Service for file format processing
    """

    def __init__(
        self,
        video_service: VideoService,
        srt_service: SRTService,
        llm_service: LLMService,
        img_service: ImageProcessingService,
        file_processing_service: FileProcessingService,
    ):
        """Initialize the DataProcessingService with required dependencies.

        Args:
            video_service: Service for handling video/audio processing
            srt_service: Service for processing SRT subtitle files
            llm_service: Service for Large Language Model operations
            img_service: Service for image processing and search
            file_processing_service: Service for various file format processing
        """
        self.video_service = video_service
        self.srt_service = srt_service
        self.llm_service = llm_service
        self.img_service = img_service
        self.file_processing_service = file_processing_service

    async def generate_paragraphs_with_visuals(
        self, srt_file: UploadFile, media_file: UploadFile
    ) -> EducationalContent:
        """Generate paragraphs with visual elements from SRT and media files.

        Args:
            srt_file: The subtitle file containing text transcriptions
            media_file: The video/audio file for timestamp alignment

        Returns:
            EducationalContent: Structured paragraphs with aligned visuals and timestamps

        Raises:
            Exception: If generated paragraphs and aligned paragraphs lengths don't match
        """
        srt_text = await self._extract_srt_text(srt_file)
        generated_output = await self._generate_paragraphs_from_transcript(srt_text)
        paragraph_items = self._create_paragraph_items(generated_output.paragraphs)
        video_alignment_result = await self._align_with_video_timestamps(
            media_file, paragraph_items
        )
        combined_result = self._merge_video_alignment_with_generated_paragraphs(
            video_paragraph_alignment_result=video_alignment_result,
            generated_output=generated_output,
        )
        return EducationalContent(paragraphs=combined_result)

    async def extract_and_align_pdf_visuals(
        self, srt_file: UploadFile, media_file: UploadFile, pdf_file: UploadFile
    ) -> EducationalContent:
        """Extract visuals from PDF and align them with paragraphs from SRT and media files.

        Args:
            srt_file: The subtitle file containing text transcriptions
            media_file: The video/audio file for timestamp alignment
            pdf_file: The PDF file containing visual elements to extract

        Returns:
            EducationalContent: Structured paragraphs with aligned PDF visuals and timestamps

        Raises:
            Exception: If generated paragraphs and aligned paragraphs lengths don't match
        """
        srt_text = await self._extract_srt_text(srt_file)
        processed_visuals = await self._extract_and_process_pdf_images(pdf_file)

        generated_output = await self._generate_paragraphs_with_visual_mapping(
            srt_text, processed_visuals
        )
        aligned_paragraphs = self._match_paragraphs_to_extracted_visuals(
            generated_output=generated_output, processed_visuals=processed_visuals
        )
        paragraph_items = self._create_paragraph_items(aligned_paragraphs.paragraphs)
        video_alignment_result = await self._align_with_video_timestamps(
            media_file, paragraph_items
        )
        combined_result = self._merge_video_alignment_with_generated_paragraphs(
            video_paragraph_alignment_result=video_alignment_result,
            generated_output=aligned_paragraphs,
        )
        return EducationalContent(paragraphs=combined_result)

    async def _extract_srt_text(self, srt_file: UploadFile) -> str:
        """Extract text content from SRT file.

        Args:
            srt_file: The subtitle file to extract text from

        Returns:
            str: The extracted text content
        """
        return await self.srt_service.extract_text(srt_file=srt_file)

    async def _generate_paragraphs_from_transcript(
        self, srt_text: str
    ) -> LLMParagraphList:
        """Generate structured paragraphs with visual metadata from transcript text.

        Args:
            srt_text: The text content from SRT file

        Returns:
            LLMParagraphList: Generated paragraphs with visual elements
        """
        formatted_prompt = self.llm_service.format_prompt(
            system_message=ParagraphWithVisualPrompt.SYSTEM_PROMPT,
            user_message=ParagraphWithVisualPrompt.USER_PROMPT,
            script=srt_text,
            output_schema=LLMParagraphList.model_json_schema(),
        )
        return await self.llm_service.ask_search_agent(
            model_name="gpt-4o",
            model_provider="openai",
            output_schema=LLMParagraphList,
            prompt=formatted_prompt,
        )

    async def _extract_and_process_pdf_images(
        self, pdf_file: UploadFile
    ) -> List[LLMVisualContent]:
        """Extract images from PDF file and process them for search.

        Args:
            pdf_file: The PDF file to extract images from

        Returns:
            List[SearchedImageVisualModel]: Processed visual models ready for alignment
        """
        pdf_bytes = await pdf_file.read()
        extracted_visuals = self.file_processing_service.extract_images_from_pdf(
            pdf_bytes=pdf_bytes
        )
        return await self.img_service.search_images(original_images=extracted_visuals)

    async def _generate_paragraphs_with_visual_mapping(
        self, srt_text: str, processed_visuals: List[LLMVisualContent]
    ) -> LLMVisualAlignmentResult:
        """Generate paragraphs with visual alignment mapping.

        Args:
            srt_text: The text content from SRT file
            processed_visuals: List of processed visual models

        Returns:
            GeneratedParagraphsVisualAlignmentModel: Generated paragraphs with visual mappings
        """
        visuals_map = [
            VisualMapping(
                visual_index=visual.visual_index, description=visual.description
            )
            for visual in processed_visuals
        ]
        formatted_prompt = self.llm_service.format_prompt(
            system_message=ParagraphAlignmentWithVisualPrompt.SYSTEM_PROMPT,
            user_message=ParagraphAlignmentWithVisualPrompt.USER_PROMPT,
            script=srt_text,
            provided_visuals=visuals_map,
            output_schema=LLMVisualAlignmentResult.model_json_schema(),
        )
        return await self.llm_service.ask_openai_llm(
            model_name="gpt-4o",
            output_schema=LLMVisualAlignmentResult,
            prompt=formatted_prompt,
        )

    def _create_paragraph_items(
        self, paragraphs: List[LLMParagraphWithVisual]
    ) -> List[ParagraphItem]:
        """Convert generated paragraphs to ParagraphItem objects.

        Args:
            paragraphs: List of paragraph objects with text and index

        Returns:
            List[ParagraphItem]: Converted paragraph items
        """
        return [
            ParagraphItem(
                text=paragraph.paragraph_text, paragraph_index=paragraph.paragraph_index
            )
            for paragraph in paragraphs
        ]

    async def _align_with_video_timestamps(
        self, media_file: UploadFile, paragraphs: List[ParagraphItem]
    ) -> MediaAlignmentResult:
        """Align paragraphs with video timestamps.

        Args:
            media_file: The video/audio file for alignment
            paragraphs: List of paragraph items to align

        Returns:
            ParagraphsAlignmentWithVideoResponse: Alignment result with timestamps
        """
        return await self.video_service.align_paragraph_with_media(
            media_file=media_file, paragraphs=paragraphs
        )

    def _merge_video_alignment_with_generated_paragraphs(
        self,
        video_paragraph_alignment_result: MediaAlignmentResult,
        generated_output: LLMParagraphList,
        # external_visuals: List[VisualContent] = None,
    ) -> List[ProcessedParagraph]:
        """Merge video alignment results with generated paragraph content.

        Args:
            video_paragraph_alignment_result: Alignment result with video timestamps
            generated_output: Generated paragraphs with visual metadata
            external_visuals: Optional list of external visual models

        Returns:
            List[ParagraphWithVisualModel]: Combined result with all data merged

        Raises:
            Exception: If generated and aligned paragraphs lengths don't match
        """
        combined_result = []
        if len(video_paragraph_alignment_result.result) != len(
            generated_output.paragraphs
        ):
            raise Exception(
                "Generated paragraphs and aligned paragraphs must be matched in length."
            )

        for paragraph in generated_output.paragraphs:
            aligned_paragraph = self._find_aligned_paragraph(
                paragraph.paragraph_index, video_paragraph_alignment_result.result
            )
            processed_visual_model = self._process_paragraph_visuals(
                paragraph, aligned_paragraph
            )
            processed_paragraph = self._create_processed_paragraph(
                paragraph, aligned_paragraph, processed_visual_model
            )
            combined_result.append(processed_paragraph)
        return combined_result

    def _find_aligned_paragraph(
        self, paragraph_index: int, aligned_results: List[AlignedParagraph]
    ) -> AlignedParagraph:
        """Find the aligned paragraph matching the given index.

        Args:
            paragraph_index: The index of the paragraph to find
            aligned_results: List of aligned paragraph results

        Returns:
            The matching aligned paragraph or None
        """
        return next(
            (
                aligned_paragraph
                for aligned_paragraph in aligned_results
                if aligned_paragraph.paragraph_index == paragraph_index
            ),
            None,
        )

    def _process_paragraph_visuals(
        self, paragraph: LLMParagraphWithVisual, aligned_paragraph: AlignedParagraph
    ):
        """Process visual data for a paragraph if it exists.

        Args:
            paragraph: The paragraph with potential visual data
            aligned_paragraph: The aligned paragraph with word timestamps

        Returns:
            Processed visual model or None
        """
        if paragraph.visuals is not None:
            return self._map_visual_to_word_timestamps(
                visual_model=paragraph.visuals,
                paragraph_words=aligned_paragraph.paragraph_words,
            )
        return None

    def _create_processed_paragraph(
        self, paragraph, aligned_paragraph, processed_visual_model
    ) -> ProcessedParagraph:
        """Create a complete paragraph model with visual and timing data.

        Args:
            paragraph: The original paragraph with text and metadata
            aligned_paragraph: The paragraph with video alignment data
            processed_visual_model: The processed visual model

        Returns:
            ParagraphWithVisualModel: Complete paragraph model
        """
        word_timestamps = [
            WordTimestamp(word=word.text, start=word.start, end=word.end)
            for word in aligned_paragraph.paragraph_words
        ]

        return ProcessedParagraph(
            paragraph_id=paragraph.paragraph_index + 1,
            text_content=paragraph.paragraph_text,
            start_time=aligned_paragraph.start,
            end_time=aligned_paragraph.end,
            keywords=paragraph.keywords,
            word_timestamps=word_timestamps,
            visual_content=processed_visual_model,
        )

    def _map_visual_to_word_timestamps(
        self,
        visual_model: LLMVisualItem,
        paragraph_words: List[WordTranscription],
    ) -> VisualContent:
        """Map visual elements to precise word timestamps within paragraphs.

        Args:
            visual_model: The visual model with start sentence information
            paragraph_words: List of word transcriptions with timestamps

        Returns:
            VisualItemModel: Visual model with precise start timestamp, or None if no match
        """
        cleaned_visual_words = self._prepare_visual_start_words(
            visual_model.start_sentence
        )

        for index in range(len(paragraph_words) - len(cleaned_visual_words) + 1):
            if self._words_match_at_position(
                cleaned_visual_words, paragraph_words, index
            ):
                return VisualContent(
                    type=visual_model.type,
                    content=visual_model.content,
                    start_time=paragraph_words[index].start,
                )
        return None

    def _prepare_visual_start_words(self, start_sentence: str) -> List[str]:
        """Prepare visual start words for matching by cleaning and splitting.

        Args:
            start_sentence: The sentence that marks the visual start

        Returns:
            List[str]: Cleaned and split words ready for matching
        """
        visual_start_words = self._clean_text(start_sentence).split(" ")
        return [word.strip() for word in visual_start_words]

    def _words_match_at_position(
        self,
        cleaned_visual_words: List[str],
        paragraph_words: List[WordTranscription],
        index: int,
    ) -> bool:
        """Check if visual words match paragraph words at a specific position.

        Args:
            cleaned_visual_words: The cleaned visual words to match
            paragraph_words: The paragraph words with timestamps
            index: The starting position to check

        Returns:
            bool: True if words match at the position
        """
        seq_words = [
            self._clean_text(word.text).strip()
            for word in paragraph_words[index : index + len(cleaned_visual_words)]
        ]
        return cleaned_visual_words == seq_words

    def _match_paragraphs_to_extracted_visuals(
        self,
        generated_output: LLMVisualAlignmentResult,
        processed_visuals: List[LLMVisualContent],
    ) -> LLMParagraphList:
        """Match generated paragraphs with their corresponding extracted visuals.

        Args:
            generated_output: Generated paragraphs with visual alignment data
            processed_visuals: List of processed visual models from PDF

        Returns:
            LLMParagraphList: Paragraphs with matched visuals
        """
        aligned_result = []
        for paragraph in generated_output.paragraphs:
            if paragraph.visual_reference is not None:
                aligned_visual = self._find_matching_visual(
                    paragraph.visual_reference.visual_index, processed_visuals
                )
                aligned_paragraph = self._create_aligned_paragraph_with_visual(
                    paragraph, aligned_visual
                )
                aligned_result.append(aligned_paragraph)
        return LLMParagraphList(paragraphs=aligned_result)

    def _find_matching_visual(
        self, visual_index: int, processed_visuals: List[LLMVisualContent]
    ):
        """Find the visual that matches the given visual index.

        Args:
            visual_index: The index of the visual to find
            processed_visuals: List of processed visual models

        Returns:
            The matching visual model or None
        """
        return next(
            (
                aligned_visual
                for aligned_visual in processed_visuals
                if aligned_visual.visual_index == visual_index
            ),
            None,
        )

    def _create_aligned_paragraph_with_visual(
        self, paragraph: LLMParagraphWithVisualRef, aligned_visual: LLMVisualContent
    ) -> LLMParagraphWithVisual:
        """Create an aligned paragraph with its associated visual.

        Args:
            paragraph: The original paragraph object
            aligned_visual: The matching visual model

        Returns:
            GeneratedParagraphWithVisualModel: Paragraph with aligned visual
        """
        new_aligned_visual = LLMVisualItem(
            type=aligned_visual.type,
            content=aligned_visual.content,
            start_sentence=paragraph.visual_reference.start_sentence,
        )
        aligned_paragraph = LLMParagraphWithVisual(
            paragraph_index=paragraph.paragraph_index,
            paragraph_text=paragraph.paragraph_text,
            keywords=paragraph.keywords,
            visuals=new_aligned_visual.model_dump(),
        )
        return aligned_paragraph

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text by removing punctuation and converting to lowercase.

        Args:
            text: The text string to clean

        Returns:
            str: Cleaned text with punctuation removed and lowercased
        """
        punctuation_table = str.maketrans("", "", string.punctuation)
        cleaned_text = text.translate(punctuation_table)
        return cleaned_text.lower()
