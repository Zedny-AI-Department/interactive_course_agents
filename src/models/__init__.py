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
    LLMsearchedVisualContent,
    LLMVisualContentWithCopyright,
    StoredVisualContent,
)
from .llm_response_models import (
    LLMGeneratedVisualItem,
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
from .interactive_db_models import (
    ImageTypeEnum,
    FileCreateSchema,
    ImageCreateSchema,
    FileResponseSchema,
    ImageResponseSchema,
    GetTypeItemResponseSchema
)
from .mapped_output_models import (
    MappedChartData,
    MappedImageData,
    MappedTableData,
    MappedVisualContent,
    MappedKeyWord,
    MappedWord,
    MappedParagraph,
    MappedEducationalContent
)
from .task_models import TaskStage, TaskData, TaskResponse, CreateTaskResponse, TaskStatus
from .video_metadata_model import AgentMode, VideoMetadataRequest, VideoMetadata
# Legacy model names - these map to new models for backward compatibility
GeneratedParagraphWithVisualListModel = LLMParagraphList
GeneratedVisualItemModel = LLMGeneratedVisualItem
GeneratedParagraphsVisualAlignmentModel = LLMVisualAlignmentResult
GeneratedParagraphVisualAlignmentModel = LLMsearchedVisualContent
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
    "LLMsearchedVisualContent",
    "LLMVisualContentWithCopyright",
    "StoredVisualContent",
    "LLMGeneratedVisualItem",
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
    "AlignedParagraph",
    "FileImageTypeEnum",

    # Interactive DB models:
    "ImageTypeEnum",
    "FileCreateSchema",
    "ImageCreateSchema", 
    "FileResponseSchema",
    "ImageResponseSchema",
    "GetTypeItemResponseSchema",

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

    # Mapped model:
    "MappedChartData",
    "MappedImageData",
    "MappedTableData",
    "MappedVisualContent",
    "MappedKeyWord",
    "MappedWord",
    "MappedParagraph",
    "MappedEducationalContent",

    # Task models
    "TaskStage",
    "TaskData",
    "TaskResponse", 
    "CreateTaskResponse", 
    "TaskStatus",

    # Video metadata models
    "AgentMode",
    "VideoMetadataRequest", 
    "VideoMetadata", 
]
