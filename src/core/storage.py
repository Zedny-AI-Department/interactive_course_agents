from typing import Optional
from supabase import create_client, Client
from app.config import settings
from app.exceptions.custom_exception import CustomException


class StorageClient:
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or settings.STORAGE_URL
        self.key = key or settings.STORAGE_KEY
        self.client: Client = create_client(self.url, self.key)

    def get_bucket(self, bucket_name: str):
        """Return a Supabase storage bucket"""
        return self.client.storage.from_(bucket_name)

    def get_image(self, bucket_name: str, file_name: str):
        """Get a file from a bucket"""
        bucket = self.get_bucket(bucket_name)
        return bucket.download(file_name)

    def get_image_url(self, bucket_name: str, file_name: str):
        """Get a public URL for a file in a bucket"""
        bucket = self.get_bucket(bucket_name)
        return bucket.get_public_url(file_name)

    def upload_file(self, bucket_name: str, file_name: str, content: bytes):
        """Upload a file to a bucket"""
        try:
            bucket = self.get_bucket(bucket_name)
            return bucket.upload(file_name, content)
        except Exception as e:
            print(e)
            raise CustomException(
                status_code=500,
                detail="Failed to upload file to storage",
                additional_info={"error": str(e), "bucket_name": bucket_name, "file_name": file_name},
                exception_type="StorageUploadError"
            )

    def download_file(self, bucket_name: str, file_name: str):
        """Download a file from a bucket"""
        bucket = self.get_bucket(bucket_name)
        return bucket.download(file_name)

    def delete_file(self, bucket_name: str, file_name: str):
        """Delete a file from a bucket"""
        bucket = self.get_bucket(bucket_name)
        return bucket.remove([file_name])
