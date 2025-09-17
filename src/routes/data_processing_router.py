from fastapi import APIRouter, File, Query, UploadFile, HTTPException

from src.container import get_data_processing_service
from src.models import ParagraphWithVisualListModel
from src.services import DataProcessingService, VideoService, LLMService, SRTService

data_processing_router = APIRouter()


# Endpoints

@data_processing_router.post("/process/srt_media/",
                             response_model=ParagraphWithVisualListModel)
async def process_data(
    srt_file: UploadFile = File(...),
    media_file: UploadFile = File(...),
):
    try:
        # Create pipeline
        service = get_data_processing_service()
        # Align paragraphs with audio
        result = await service.run_generation_agent(media_file=media_file, srt_file=srt_file)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )


@data_processing_router.post("/process/srt_media/extract",
                             )
async def process_data(
    srt_file: UploadFile = File(...),
    media_file: UploadFile = File(...),
    image_file: UploadFile = File(...)
):
    try:
        # Create pipeline
        service = get_data_processing_service()
        # Align paragraphs with audio
        result = await service.run_extracting_agent(media_file=media_file, srt_file=srt_file, pdf_file=image_file)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )