from src.services import (
    VideoService,
    LLMService,
    SRTService,
    DataProcessingService,
    ImageService,
    FileService,
    StorageService,
    BackgroundProcessor,
)


def get_video_service():
    return VideoService()


def get_llm_service():
    return LLMService()


def get_srt_service():
    return SRTService()


def get_image_service():
    return ImageService(llm_service=get_llm_service())


def get_file_service():
    return FileService()


def get_storage_service():
    return StorageService()


def get_data_processing_service():
    return DataProcessingService(
        video_service=get_video_service(),
        llm_service=get_llm_service(),
        srt_service=get_srt_service(),
        img_service=get_image_service(),
        file_processing_service=get_file_service(),
        storage_service=get_storage_service()
    )


def get_background_processor():
    return BackgroundProcessor(
        img_service=get_image_service(),
        data_processing_service=get_data_processing_service(),
    )
