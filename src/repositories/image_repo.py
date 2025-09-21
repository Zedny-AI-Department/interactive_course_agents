from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image_model import ImageModel
from app.repositories.base_repo import BaseRepository


class ImageRepository(BaseRepository[ImageModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(ImageModel, db)
