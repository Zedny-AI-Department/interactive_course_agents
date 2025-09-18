# Main model imports - use these in new code
from .base_models import StrictBaseModel, KeywordItem, WordTimestamp, TimestampedContent
from .visual_content_models import (
    TableContent,
    ChartDataset,
    ChartContent,
    ImageContent,
    VisualContent,
    ExtractedImage,
    VisualMapping,
    LLMVisualContent,
)
from .llm_response_models import (
    LLMVisualItem,
    LLMParagraphBase,
    LLMParagraphWithVisual,
    LLMParagraphList,
    LLMVisualReference,
    LLMParagraphWithVisualRef,
    LLMVisualAlignmentResult,
)
from .transcription_output_model import (
    TranscribedSegment,
    AudioSegment,
    WordTranscription,
    DetailedTranscription,
    ScoredMatch,
    AlignedParagraph,
    MediaAlignmentResult,
    ParagraphItem,
    AlignedParagraph,
)
from .final_output_models import ProcessedParagraph, EducationalContent

# Legacy model names - these map to new models for backward compatibility
GeneratedParagraphWithVisualListModel = LLMParagraphList
GeneratedVisualItemModel = LLMVisualItem
GeneratedParagraphsVisualAlignmentModel = LLMVisualAlignmentResult
GeneratedParagraphVisualAlignmentModel = LLMParagraphWithVisualRef
GeneratedParagraphWithVisualModel = LLMParagraphWithVisual
ParagraphWithVisualListModel = EducationalContent
ParagraphWithVisualModel = ProcessedParagraph
VisualItemModel = VisualContent
WordTimestampModel = WordTimestamp
SegmentTranscriptionModelWithWords = DetailedTranscription
WordTranscriptionModel = WordTranscription
ParagraphsAlignmentWithVideoResponse = MediaAlignmentResult
VisualMappingModel = VisualMapping
ExtractedImageModel = ExtractedImage
DescribedVisualModel = VisualContent
SearchedImageVisualModel = VisualContent

__all__ = [
    # New organized models - use these in new code
    "StrictBaseModel",
    "KeywordItem",
    "WordTimestamp",
    "TimestampedContent",
    "TableContent",
    "ChartDataset",
    "ChartContent",
    "ImageContent",
    "VisualContent",
    "ExtractedImage",
    "VisualMapping",
    "LLMVisualContent",
    "LLMVisualItem",
    "LLMParagraphBase",
    "LLMParagraphWithVisual",
    "LLMParagraphList",
    "LLMVisualReference",
    "LLMParagraphWithVisualRef",
    "LLMVisualAlignmentResult",
    "TranscribedSegment",
    "AudioSegment",
    "WordTranscription",
    "DetailedTranscription",
    "ScoredMatch",
    "AlignedParagraph",
    "MediaAlignmentResult",
    "ParagraphItem",
    "ProcessedParagraph",
    "EducationalContent",
    "AlignedParagraph"
    # Legacy model names for backward compatibility
    "SegmentTranscriptionModelWithWords",
    "WordTranscriptionModel",
    "ParagraphsAlignmentWithVideoResponse",
    "GeneratedParagraphWithVisualListModel",
    "GeneratedVisualItemModel",
    "GeneratedParagraphsVisualAlignmentModel",
    "GeneratedParagraphVisualAlignmentModel",
    "GeneratedParagraphWithVisualModel",
    "ParagraphWithVisualListModel",
    "ParagraphWithVisualModel",
    "VisualItemModel",
    "WordTimestampModel",
    "VisualMappingModel",
    "ExtractedImageModel",
    "DescribedVisualModel",
    "SearchedImageVisualModel",
]
