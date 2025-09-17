import asyncio
from typing import Dict, Any
from fastapi import UploadFile
import tempfile
import os

from src.services.task_manager_service import task_manager
from src.services.data_processing_service import DataProcessingService
from src.services import VideoService, LLMService, SRTService
from src.models.task_models import TaskStatus, TaskStage


class BackgroundProcessor:
    """Handles background processing of video tasks."""
    
    def __init__(self):
        self.data_processing_service = None
    
    def _get_data_processing_service(self) -> DataProcessingService:
        """Get or create data processing service instance."""
        if not self.data_processing_service:
            video_service = VideoService()
            llm_service = LLMService()
            srt_service = SRTService()
            self.data_processing_service = DataProcessingService(
                video_service=video_service,
                llm_service=llm_service,
                srt_service=srt_service,
            )
        return self.data_processing_service
    
    async def process_srt_media_task(
        self, 
        task_id: str, 
        srt_file_content: bytes, 
        srt_filename: str,
        media_file_content: bytes, 
        media_filename: str,
        media_content_type: str
    ):
        """Process SRT and media files in background."""
        try:
            # Update task status to processing
            await task_manager.update_task_status(
                task_id, 
                TaskStatus.PROCESSING, 
                TaskStage.TRANSCRIBING, 
                progress=10
            )
            
            # Create temporary files for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as srt_temp, \
                 tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(media_filename)[1]) as media_temp:
                
                # Write file contents to temp files
                srt_temp.write(srt_file_content)
                media_temp.write(media_file_content)
                srt_temp.flush()
                media_temp.flush()
                
                # Create UploadFile objects for processing
                srt_upload = UploadFile(
                    filename=srt_filename,
                    file=open(srt_temp.name, 'rb')
                )
                media_upload = UploadFile(
                    filename=media_filename,
                    file=open(media_temp.name, 'rb'),
                    # content_type = str(media_content_type)
                )

                try:
                    # Update progress - starting processing
                    await task_manager.update_task_status(
                        task_id, 
                        TaskStatus.PROCESSING, 
                        TaskStage.PROCESSING_LLM, 
                        progress=30
                    )
                    
                    # Get processing service
                    service = self._get_data_processing_service()
                    
                    # Update progress - aligning with video
                    await task_manager.update_task_status(
                        task_id, 
                        TaskStatus.PROCESSING, 
                        TaskStage.ALIGNING, 
                        progress=70
                    )
                    
                    # Process the files
                    result = await service.process_srt_file(
                        media_file=media_upload, 
                        srt_file=srt_upload
                    )
                    
                    # Convert result to dict for JSON storage
                    result_dict = result.model_dump() if hasattr(result, 'model_dump') else dict(result)
                    
                    # Update task as completed
                    await task_manager.update_task_status(
                        task_id, 
                        TaskStatus.COMPLETED, 
                        TaskStage.COMPLETED, 
                        progress=100,
                        result=result_dict
                    )
                    
                finally:
                    # Close file handles
                    srt_upload.file.close()
                    media_upload.file.close()
                    
                    # Clean up temporary files
                    try:
                        os.unlink(srt_temp.name)
                        os.unlink(media_temp.name)
                    except OSError:
                        pass  # File already deleted
                        
        except Exception as e:
            # Update task as failed
            await task_manager.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                progress=0,
                error_message=str(e)
            )
            raise


background_processor = BackgroundProcessor()