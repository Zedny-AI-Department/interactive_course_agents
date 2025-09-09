from fastapi import APIRouter, File, Query, UploadFile, HTTPException

from src.models import ParagraphWithVisualListModel
from src.services import DataProcessingService, VideoService, LLMService, SRTService

data_processing_router = APIRouter()


# Pipeline
def build_pipeline():
    # Your pipeline building logic here
    video_service = VideoService()
    llm_service = LLMService()
    srt_service = SRTService()
    data_processing_service = DataProcessingService(
        video_service=video_service,
        llm_service=llm_service,
        srt_service=srt_service,
    )
    return data_processing_service

# Endpoints

@data_processing_router.post("/process/srt_media/",
                             response_model=ParagraphWithVisualListModel)
async def process_data(
    srt_file: UploadFile = File(...),
    media_file: UploadFile = File(...),
):
    try:
        # Create pipeline
        service = build_pipeline()
        # Align paragraphs with audio
        result = await service.process_srt_file(media_file=media_file, srt_file=srt_file) 
        print("finished")
        return result
    except Exception as e:
        raise e
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )
