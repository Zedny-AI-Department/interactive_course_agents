from sqlalchemy.ext.asyncio import AsyncSession

from app.models.files_model import FileModel
from app.repositories.base_repo import BaseRepository


class FileRepository(BaseRepository[FileModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(FileModel, db)
