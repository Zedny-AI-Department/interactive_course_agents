from fastapi import APIRouter, File, Query, UploadFile, HTTPException

from src.container import get_data_processing_service
from src.models import EducationalContent


data_processing_router = APIRouter()


# Endpoints


@data_processing_router.post(
    "/educational-content/generate", response_model=EducationalContent
)
async def generate_educational_content(
    srt_file: UploadFile = File(..., description="SRT subtitle file"),
    media_file: UploadFile = File(..., description="Video or audio media file"),
):
    try:
        # Create pipeline
        service = get_data_processing_service()
        # Align paragraphs with audio
        result = await service.generate_paragraphs_with_visuals(
            media_file=media_file, srt_file=srt_file
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )


@data_processing_router.post(
    "/educational-content/extract-pdf-visuals", response_model=EducationalContent
)
async def extract_pdf_visuals_and_align(
    srt_file: UploadFile = File(..., description="SRT subtitle file"),
    media_file: UploadFile = File(..., description="Video or audio media file"),
    pdf_file: UploadFile = File(..., description="PDF file containing visual elements"),
):
    try:
        # Create pipeline
        service = get_data_processing_service()
        # Align paragraphs with audio
        result = await service.extract_and_align_pdf_visuals(
            media_file=media_file, srt_file=srt_file, pdf_file=pdf_file
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}",
        )
