from fastapi import UploadFile
import tempfile
import os
import httpx

from src.services.task_manager_service import task_manager
from src.services.data_processing_service import DataProcessingService
from src.services import ImageService
from src.models.task_models import TaskStatus, TaskStage


class BackgroundProcessor:
    """Handles background processing of video tasks."""

    def __init__(
        self, img_service: ImageService, data_processing_service: DataProcessingService
    ):
        self.img_service = img_service
        self.data_processing_service = data_processing_service

    async def generate_paragraphs_with_visuals_task(
        self,
        task_id: str,
        srt_file_content: bytes,
        srt_filename: str,
        media_file_content: bytes,
        media_filename: str,
        media_content_type: str,
    ):
        """Process SRT and media files to generate paragraphs with visuals in background."""
        try:
            # Get task data to retrieve video metadata
            task_data = await task_manager.get_task_status(task_id)
            video_metadata = task_data.video_metadata if task_data else None
            
            # Update task status to processing
            await task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING, TaskStage.TRANSCRIBING, progress=10
            )

            # Create temporary files for processing
            with (
                tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as srt_temp,
                tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(media_filename)[1]
                ) as media_temp,
            ):

                # Write file contents to temp files
                srt_temp.write(srt_file_content)
                media_temp.write(media_file_content)
                srt_temp.flush()
                media_temp.flush()

                # Create UploadFile objects for processing
                srt_upload = UploadFile(
                    filename=srt_filename, file=open(srt_temp.name, "rb")
                )
                media_upload = UploadFile(
                    filename=media_filename, file=open(media_temp.name, "rb")
                )

                try:
                    # Update progress - starting processing
                    await task_manager.update_task_status(
                        task_id,
                        TaskStatus.PROCESSING,
                        TaskStage.PROCESSING_LLM,
                        progress=30,
                    )

                    # Update progress - aligning with video
                    await task_manager.update_task_status(
                        task_id, TaskStatus.PROCESSING, TaskStage.ALIGNING, progress=70
                    )

                    # Process the files
                    result = await self.data_processing_service.generate_paragraphs_with_visuals(
                        media_file=media_upload, srt_file=srt_upload, video_metadata=video_metadata
                    )

                    # Convert result to dict for JSON storage
                    result_dict = (
                        result.model_dump()
                        if hasattr(result, "model_dump")
                        else dict(result)
                    )

                    # Update task as completed
                    await task_manager.update_task_status(
                        task_id,
                        TaskStatus.COMPLETED,
                        TaskStage.COMPLETED,
                        progress=100,
                        result=result_dict,
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
                task_id, TaskStatus.FAILED, progress=0, error_message=str(e)
            )
            raise

    async def extract_and_align_pdf_visuals_task(
        self,
        task_id: str,
        srt_file_content: bytes,
        srt_filename: str,
        media_file_content: bytes,
        media_filename: str,
        pdf_file_content: bytes,
        pdf_filename: str,
    ):
        """Extract and align PDF visuals with SRT and media files in background."""
        try:
            # Get task data to retrieve video metadata
            task_data = await task_manager.get_task_status(task_id)
            video_metadata = task_data.video_metadata if task_data else None
            
            # Update task status to processing
            await task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING, TaskStage.TRANSCRIBING, progress=10
            )

            # Create temporary files for processing
            with (
                tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as srt_temp,
                tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(media_filename)[1]
                ) as media_temp,
                tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_temp,
            ):

                # Write file contents to temp files
                srt_temp.write(srt_file_content)
                media_temp.write(media_file_content)
                pdf_temp.write(pdf_file_content)
                srt_temp.flush()
                media_temp.flush()
                pdf_temp.flush()

                # Create UploadFile objects for processing
                srt_upload = UploadFile(
                    filename=srt_filename, file=open(srt_temp.name, "rb")
                )
                media_upload = UploadFile(
                    filename=media_filename, file=open(media_temp.name, "rb")
                )
                pdf_upload = UploadFile(
                    filename=pdf_filename, file=open(pdf_temp.name, "rb")
                )

                try:
                    # Update progress - starting processing
                    await task_manager.update_task_status(
                        task_id,
                        TaskStatus.PROCESSING,
                        TaskStage.PROCESSING_LLM,
                        progress=30,
                    )

                    # Update progress - aligning with video
                    await task_manager.update_task_status(
                        task_id, TaskStatus.PROCESSING, TaskStage.ALIGNING, progress=70
                    )

                    # Process the files
                    result = await self.data_processing_service.extract_and_align_pdf_visuals(
                        media_file=media_upload,
                        srt_file=srt_upload,
                        pdf_file=pdf_upload,
                        video_metadata=video_metadata,
                    )

                    # Convert result to dict for JSON storage
                    result_dict = (
                        result.model_dump()
                        if hasattr(result, "model_dump")
                        else dict(result)
                    )

                    # Update task as completed
                    await task_manager.update_task_status(
                        task_id,
                        TaskStatus.COMPLETED,
                        TaskStage.COMPLETED,
                        progress=100,
                        result=result_dict,
                    )

                finally:
                    # Close file handles
                    srt_upload.file.close()
                    media_upload.file.close()
                    pdf_upload.file.close()

                    # Clean up temporary files
                    try:
                        os.unlink(srt_temp.name)
                        os.unlink(media_temp.name)
                        os.unlink(pdf_temp.name)
                    except OSError:
                        pass  # File already deleted

        except Exception as e:
            # Update task as failed
            await task_manager.update_task_status(
                task_id, TaskStatus.FAILED, progress=0, error_message=str(e)
            )
            raise

    async def extract_and_align_pdf_visuals_with_copyright_task(
        self,
        task_id: str,
        srt_file_content: bytes,
        srt_filename: str,
        media_file_content: bytes,
        media_filename: str,
        pdf_file_content: bytes,
        pdf_filename: str,
    ):
        """Extract and align PDF visuals with copyright detection in background."""
        try:
            # Get task data to retrieve video metadata
            task_data = await task_manager.get_task_status(task_id)
            video_metadata = task_data.video_metadata if task_data else None
            
            # Update task status to processing
            await task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING, TaskStage.TRANSCRIBING, progress=10
            )

            # Create temporary files for processing
            with (
                tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as srt_temp,
                tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(media_filename)[1]
                ) as media_temp,
                tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_temp,
            ):

                # Write file contents to temp files
                srt_temp.write(srt_file_content)
                media_temp.write(media_file_content)
                pdf_temp.write(pdf_file_content)
                srt_temp.flush()
                media_temp.flush()
                pdf_temp.flush()

                # Create UploadFile objects for processing
                srt_upload = UploadFile(
                    filename=srt_filename, file=open(srt_temp.name, "rb")
                )
                media_upload = UploadFile(
                    filename=media_filename, file=open(media_temp.name, "rb")
                )
                pdf_upload = UploadFile(
                    filename=pdf_filename, file=open(pdf_temp.name, "rb")
                )

                try:
                    # Update progress - starting processing
                    await task_manager.update_task_status(
                        task_id,
                        TaskStatus.PROCESSING,
                        TaskStage.PROCESSING_LLM,
                        progress=30,
                    )

                    # Update progress - aligning with video
                    await task_manager.update_task_status(
                        task_id, TaskStatus.PROCESSING, TaskStage.ALIGNING, progress=70
                    )

                    # Process the files
                    result = await self.data_processing_service.extract_and_align_pdf_visuals_with_copyright_detection(
                        media_file=media_upload,
                        srt_file=srt_upload,
                        pdf_file=pdf_upload,
                        video_metadata=video_metadata,
                    )

                    # Convert result to dict for JSON storage
                    result_dict = (
                        result.model_dump()
                        if hasattr(result, "model_dump")
                        else dict(result)
                    )

                    # Update task as completed
                    await task_manager.update_task_status(
                        task_id,
                        TaskStatus.COMPLETED,
                        TaskStage.COMPLETED,
                        progress=100,
                        result=result_dict,
                    )

                finally:
                    # Close file handles
                    srt_upload.file.close()
                    media_upload.file.close()
                    pdf_upload.file.close()

                    # Clean up temporary files
                    try:
                        os.unlink(srt_temp.name)
                        os.unlink(media_temp.name)
                        os.unlink(pdf_temp.name)
                    except OSError:
                        pass  # File already deleted

        except Exception as e:
            # Update task as failed
            await task_manager.update_task_status(
                task_id, TaskStatus.FAILED, progress=0, error_message=str(e)
            )
            raise

    async def convert_image_to_3d_task(
        self,
        task_id: str,
        image_file_content: bytes,
        image_filename: str,
        geometry_format: str = "glb",
        quality: str = "medium",
    ):
        """Convert image to 3D model in background."""
        try:
            # Update task status to processing
            await task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING, TaskStage.PROCESSING_LLM, progress=20
            )

            # Create temporary file for the image
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(image_filename)[1]
            ) as image_temp:
                # Write file content to temp file
                image_temp.write(image_file_content)
                image_temp.flush()

                try:
                    # Update progress - starting 3D conversion
                    await task_manager.update_task_status(
                        task_id,
                        TaskStatus.PROCESSING,
                        TaskStage.PROCESSING_LLM,
                        progress=50,
                    )

                    # Update progress - processing 3D model
                    await task_manager.update_task_status(
                        task_id, TaskStatus.PROCESSING, TaskStage.ALIGNING, progress=80
                    )

                    # Convert image to 3D
                    result = await self.img_service.convert_image_to_3d(
                        image_path=image_temp.name,
                        geometry_format=geometry_format,
                        quality=quality,
                    )

                    # Update task as completed
                    await task_manager.update_task_status(
                        task_id,
                        TaskStatus.COMPLETED,
                        TaskStage.COMPLETED,
                        progress=100,
                        result={
                            "success": True,
                            "message": "Image successfully converted to 3D",
                            "result": result,
                            "input_filename": image_filename,
                            "geometry_format": geometry_format,
                            "quality": quality,
                        },
                    )

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(image_temp.name)
                    except OSError:
                        pass  # File already deleted

        except Exception as e:
            # Update task as failed
            await task_manager.update_task_status(
                task_id, TaskStatus.FAILED, progress=0, error_message=str(e)
            )
            raise

    async def convert_image_url_to_3d_task(
        self,
        task_id: str,
        image_url: str,
        geometry_format: str = "glb",
        quality: str = "medium",
    ):
        """Convert image from URL to 3D model in background."""
        try:
            # Update task status to processing - downloading image
            await task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING, TaskStage.TRANSCRIBING, progress=20
            )

            # Download image from URL
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_content = response.content

                # Determine file extension from content-type or URL
                content_type = response.headers.get("content-type", "")
                if "image/jpeg" in content_type or "image/jpg" in content_type:
                    file_extension = ".jpg"
                elif "image/png" in content_type:
                    file_extension = ".png"
                elif "image/webp" in content_type:
                    file_extension = ".webp"
                else:
                    # Fallback to URL extension or default to .jpg
                    file_extension = os.path.splitext(image_url)[1] or ".jpg"

            # Update task status to processing - converting to 3D
            await task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING, TaskStage.PROCESSING_LLM, progress=40
            )

            # Create temporary file for the downloaded image
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_extension
            ) as image_temp:
                # Write image content to temp file
                image_temp.write(image_content)
                image_temp.flush()

                try:
                    # Update progress - processing 3D model
                    await task_manager.update_task_status(
                        task_id, TaskStatus.PROCESSING, TaskStage.ALIGNING, progress=80
                    )

                    # Convert image to 3D using local file path
                    result = await self.img_service.convert_image_to_3d(
                        image_path=image_temp.name,
                        geometry_format=geometry_format,
                        quality=quality,
                    )

                    # Update task as completed
                    await task_manager.update_task_status(
                        task_id,
                        TaskStatus.COMPLETED,
                        TaskStage.COMPLETED,
                        progress=100,
                        result={
                            "success": True,
                            "message": "Image successfully converted to 3D",
                            "result": result,
                            "input_url": image_url,
                            "geometry_format": geometry_format,
                            "quality": quality,
                        },
                    )

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(image_temp.name)
                    except OSError:
                        pass  # File already deleted
        except Exception as e:
            # Update task as failed
            await task_manager.update_task_status(
                task_id, TaskStatus.FAILED, progress=0, error_message=str(e)
            )
            raise

