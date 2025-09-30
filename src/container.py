from src.clients import InteractiveDBClient
from src.repositories import InteractiveDBRepository
from src.services import (
    VideoService,
    LLMService,
    SRTService,
    DataProcessingService,
    ImageService,
    FileService,
    BackgroundProcessor,
)
from src.config import settings

# Client
def get_interactive_db_client():
    return InteractiveDBClient(api_base_url=settings.STORAGE_API_URL)

# Repositories

def get_interactive_db_repository():
    return InteractiveDBRepository(interactive_db_client=get_interactive_db_client())

def get_video_service():
    return VideoService()


def get_llm_service():
    return LLMService()


def get_srt_service():
    return SRTService()


def get_image_service():
    return ImageService(llm_service=get_llm_service(), interactive_db_repository=get_interactive_db_repository())


def get_file_service():
    return FileService()

def get_data_processing_service():
    return DataProcessingService(
        interactive_db_repository=get_interactive_db_repository(),
        video_service=get_video_service(),
        llm_service=get_llm_service(),
        srt_service=get_srt_service(),
        img_service=get_image_service(),
        file_processing_service=get_file_service()
    )


def get_background_processor():
    return BackgroundProcessor(
        img_service=get_image_service(),
        data_processing_service=get_data_processing_service(),
    )
