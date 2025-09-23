import os
import uuid
import hashlib
from typing import Optional, Dict, Any, List
from fastapi import UploadFile, HTTPException
from datetime import datetime
import json

from src.client.storage import StorageClient
from src.models.db_models import FileModel, FileTypeModel, ImageModel, ProcessingStatusEnum, ImageTypeEnum
from src.client.database import Database


class FileStorageService:
    def __init__(self, storage_client: StorageClient, database: Database):
        self.storage_client = storage_client
        self.database = database
        
    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename to prevent conflicts."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        name, ext = os.path.splitext(original_filename)
        return f"{timestamp}_{unique_id}_{name}{ext}"
        
    async def _get_file_type_by_name(self, type_name: str, session) -> Optional[FileTypeModel]:
        """Get file type by name."""
        from sqlalchemy import select
        result = await session.execute(
            select(FileTypeModel).where(FileTypeModel.name == type_name)
        )
        return result.scalar_one_or_none()
    
    async def save_video_file(
        self, 
        video_file: UploadFile, 
        course_name: Optional[str] = None,
        bucket_name: str = "videos"
    ) -> FileModel:
        """Save video file to storage and create database record."""
        return await self._save_file(
            file=video_file,
            file_type_name="video",
            course_name=course_name,
            bucket_name=bucket_name
        )
    
    async def save_srt_file(
        self, 
        srt_file: UploadFile, 
        course_name: Optional[str] = None,
        bucket_name: str = "subtitles"
    ) -> FileModel:
        """Save SRT file to storage and create database record."""
        return await self._save_file(
            file=srt_file,
            file_type_name="srt",
            course_name=course_name,
            bucket_name=bucket_name
        )
    
    async def save_pdf_file(
        self, 
        pdf_file: UploadFile, 
        course_name: Optional[str] = None,
        bucket_name: str = "documents"
    ) -> FileModel:
        """Save PDF file to storage and create database record."""
        return await self._save_file(
            file=pdf_file,
            file_type_name="pdf",
            course_name=course_name,
            bucket_name=bucket_name
        )
    
    async def _save_file(
        self,
        file: UploadFile,
        file_type_name: str,
        course_name: Optional[str] = None,
        bucket_name: str = "files"
    ) -> FileModel:
        """Generic method to save any file type."""
        async with self.database.get_session() as session:
            try:
                # Get file type
                file_type = await self._get_file_type_by_name(file_type_name, session)
                if not file_type:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"File type '{file_type_name}' not found"
                    )
                
                # Read file content
                content = await file.read()
                unique_filename = self._generate_unique_filename(file.filename)
                checksum = self._calculate_checksum(content)
                
                # Upload to storage
                storage_path = f"{course_name}/{unique_filename}" if course_name else unique_filename
                upload_result = self.storage_client.upload_file(
                    bucket_name=bucket_name,
                    file_name=storage_path,
                    content=content
                )
                
                # Get public URL
                file_url = self.storage_client.get_image_url(bucket_name, storage_path)
                
                # Create database record
                file_record = FileModel(
                    file_name=unique_filename,
                    original_file_name=file.filename,
                    course_name=course_name,
                    file_type_id=file_type.id,
                    storage_name="supabase",
                    storage_bucket=bucket_name,
                    storage_path=storage_path,
                    file_url=file_url,
                    file_size=len(content),
                    content_type=file.content_type,
                    checksum=checksum,
                    processing_status=ProcessingStatusEnum.PENDING
                )
                
                session.add(file_record)
                await session.commit()
                await session.refresh(file_record)
                
                return file_record
                
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save file: {str(e)}"
                )
    
    async def save_extracted_image(
        self,
        image_content: bytes,
        image_name: str,
        file_id: uuid.UUID,
        image_type: ImageTypeEnum,
        width: Optional[int] = None,
        height: Optional[int] = None,
        content_type: str = "image/png",
        bucket_name: str = "extracted-images"
    ) -> ImageModel:
        """Save extracted image to storage and create database record."""
        async with self.database.get_session() as session:
            try:
                # Generate unique filename
                unique_filename = self._generate_unique_filename(image_name)
                storage_path = f"extracted/{unique_filename}"
                
                # Upload to storage
                upload_result = self.storage_client.upload_file(
                    bucket_name=bucket_name,
                    file_name=storage_path,
                    content=image_content
                )
                
                # Get public URL
                image_url = self.storage_client.get_image_url(bucket_name, storage_path)
                
                # Create database record
                image_record = ImageModel(
                    file_id=file_id,
                    image_name=unique_filename,
                    original_image_name=image_name,
                    image_type=image_type,
                    storage_name="supabase",
                    storage_bucket=bucket_name,
                    storage_path=storage_path,
                    image_url=image_url,
                    image_size=len(image_content),
                    content_type=content_type,
                    width=width,
                    height=height
                )
                
                session.add(image_record)
                await session.commit()
                await session.refresh(image_record)
                
                return image_record
                
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save extracted image: {str(e)}"
                )
    
    async def update_processing_status(
        self,
        file_id: uuid.UUID,
        status: ProcessingStatusEnum,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update file processing status."""
        async with self.database.get_session() as session:
            try:
                from sqlalchemy import select
                result = await session.execute(
                    select(FileModel).where(FileModel.id == file_id)
                )
                file_record = result.scalar_one_or_none()
                
                if not file_record:
                    raise HTTPException(
                        status_code=404,
                        detail="File not found"
                    )
                
                file_record.processing_status = status
                if error_message:
                    file_record.processing_error = error_message
                if metadata:
                    file_record.processing_metadata = json.dumps(metadata)
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update processing status: {str(e)}"
                )
    
    async def get_file_by_id(self, file_id: uuid.UUID) -> Optional[FileModel]:
        """Get file record by ID."""
        async with self.database.get_session() as session:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            result = await session.execute(
                select(FileModel)
                .options(selectinload(FileModel.file_type), selectinload(FileModel.images))
                .where(FileModel.id == file_id)
            )
            return result.scalar_one_or_none()
    
    async def get_files_by_course(self, course_name: str) -> List[FileModel]:
        """Get all files for a specific course."""
        async with self.database.get_session() as session:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            result = await session.execute(
                select(FileModel)
                .options(selectinload(FileModel.file_type), selectinload(FileModel.images))
                .where(FileModel.course_name == course_name)
            )
            return result.scalars().all()
    
    async def delete_file(self, file_id: uuid.UUID) -> bool:
        """Delete file from both storage and database."""
        async with self.database.get_session() as session:
            try:
                # Get file record
                file_record = await self.get_file_by_id(file_id)
                if not file_record:
                    return False
                
                # Delete from storage
                self.storage_client.delete_file(
                    bucket_name=file_record.storage_bucket,
                    file_name=file_record.storage_path
                )
                
                # Delete associated images from storage
                for image in file_record.images:
                    self.storage_client.delete_file(
                        bucket_name=image.storage_bucket,
                        file_name=image.storage_path
                    )
                
                # Delete from database (cascades to images)
                from sqlalchemy import select
                result = await session.execute(
                    select(FileModel).where(FileModel.id == file_id)
                )
                file_to_delete = result.scalar_one_or_none()
                if file_to_delete:
                    await session.delete(file_to_delete)
                    await session.commit()
                
                return True
                
            except Exception as e:
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete file: {str(e)}"
                )