from typing import List
from fastapi import UploadFile
import asyncio

from src.models.processed_data_model import WordTimestampModel
from src.services import VideoService, SRTService, LLMService
from src.models import (
    GeneratedParagraphWithVisualListModel,
    ParagraphWithVisualListModel,
    ParagraphWithVisualModel,
    SegmentTranscriptionModelWithWords,
    GeneratedVisualItemModel,
    VisualItemModel,
    WordTranscriptionModel
)
from src.constants import ParagraphWithVisualPrompt


class DataProcessingService:
    """A service that handles interactions with data processing tools."""

    def __init__(
        self,
        video_service: VideoService,
        srt_service: SRTService,
        llm_service: LLMService,
    ):
        self.video_service = video_service
        self.srt_service = srt_service
        self.llm_service = llm_service

    async def process_srt_file(
        self, srt_file: UploadFile, media_file: UploadFile
    ) -> ParagraphWithVisualListModel:
        """Process the SRT file and media file to produce aligned output."""
        # Extract transcript with timestamps from media file
        transcript_task = asyncio.create_task(
                self.video_service.extract_transcript_with_timestamps(video_file=media_file)
            )
        # Extract text from SRT file
        srt_text = await self.srt_service.extract_text(srt_file=srt_file)
        # Generate paragraphs with metadata using LLM service
        formatted_prompt = self.llm_service.format_prompt(
            system_message=ParagraphWithVisualPrompt.SYSTEM_PROMPT,
            user_message=ParagraphWithVisualPrompt.USER_PROMPT,
            script=srt_text,
        )
        generated_output_task = asyncio.create_task(
                self.llm_service.ask_openai_llm(
                    output_schema=GeneratedParagraphWithVisualListModel,
                    prompt=formatted_prompt,
                )
            )

        # Wait for both tasks (transcript + generated output)
        transcript_with_timestamps, generated_output = await asyncio.gather(
            transcript_task, generated_output_task
        )
        combined_result = self._combine_results(
            transcription_with_timestamps=transcript_with_timestamps, aligned_output=generated_output
        )
        return ParagraphWithVisualListModel(paragraphs=combined_result)

    def _combine_results(
        self,
        transcription_with_timestamps: SegmentTranscriptionModelWithWords,
        aligned_output: GeneratedParagraphWithVisualListModel,
    ) -> List[ParagraphWithVisualModel]:
        """Combine the results from the transcript and aligned output."""
        paragraph_start_word_index = 0
        combined_result = []
        words = transcription_with_timestamps.words
        # Combine info data for each paragraph
        for paragraph in aligned_output.paragraphs:
            paragraph_text = paragraph.paragraph_text
            paragraph_end_word_index = len(paragraph_text.split())

            # Check paragraph words for matching start and end
            if (
                (words[paragraph_start_word_index].text.strip()
                == paragraph_text.split(" ")[0].strip())
                and (words[paragraph_end_word_index - 1].text.strip()
                == paragraph_text.split(" ")[-1].strip())
            ):
                paragraph_words = words[
                    paragraph_start_word_index:paragraph_end_word_index
                ]

            # Prepare visual time
            if paragraph.visuals is not None:
                print(f"{paragraph.paragraph_index}: {paragraph.visuals}")
                processed_visual_model = self._prepare_visual_data(
                    visual_model=paragraph.visuals, paragraph_words=words
                )
                print(f"proccessed: {processed_visual_model}")
            else:
                processed_visual_model = None

            paragraph_model = ParagraphWithVisualModel(
                paragraph_id=paragraph.paragraph_index,
                paragraph_text=paragraph_text,
                start_time=paragraph_words[0].start,
                end_time=paragraph_words[-1].end,
                visuals=processed_visual_model,
                words=[
                    WordTimestampModel(**{
                        "word": word.text,
                        "start": word.start,
                        "end": word.end,
                    })
                    for word in paragraph_words
                ],
                keywords=[keyword.model_dump() for keyword in paragraph.keywords],
            )
            combined_result.append(paragraph_model)
            paragraph_start_word_index = paragraph_end_word_index
        return combined_result

    def _prepare_visual_data(
        self,
        visual_model: GeneratedVisualItemModel,
        paragraph_words: List[WordTranscriptionModel],
    ) -> VisualItemModel:
        """Prepare the visual model for use in the service."""
        visual_start_words = visual_model.start_sentence.split()
        visual_start_words = [word.strip()
                              for word in visual_start_words]
        for index in range(len(paragraph_words) - len(visual_start_words) + 1):
            seq_words = [
                word.text.strip()
                for word in paragraph_words[index : index + len(visual_start_words)]
            ]
            if visual_start_words == seq_words:
                processed_visual_model = VisualItemModel(
                    type=visual_model.type,
                    content=visual_model.content,
                    start_time=paragraph_words[index].start,
                )
                return processed_visual_model
        raise ValueError(
            f"No matching sequence found for visual model start_sentence='{visual_model.start_sentence}'"
        )
