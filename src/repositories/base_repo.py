from typing import TypeVar, Generic, Type, Optional, List, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.client.database import Base
from app.exceptions.repo_exception import RepoException

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: UUID) -> Optional[T]:
        try:
            result = await self.db.execute(
                select(self.model).filter(self.model.id == id)
            )
            return result.scalars().first()
        except Exception as e:
            raise RepoException(
                status_code=500,
                detail="Error retrieving object",
                additional_info={"error": str(e), "id": str(id)}
            )

    async def get_all(
        self,
        page: int = 1,
        limit: int = 10
    ) -> List[T]:
        try:
            stmt = select(self.model)

            if page > 1:
                stmt = stmt.offset((page - 1) * limit)
            if limit is not None:
                stmt = stmt.limit(limit)

            result = await self.db.execute(stmt)
            return cast(List[T], result.scalars().all())
        except Exception as e:
            raise RepoException(
                status_code=500,
                detail="Error retrieving objects",
                additional_info={"error": str(e), "page": page, "limit": limit}
            )

    async def create(self, obj_in: dict) -> T:
        try:
            print('Processing file:', obj_in)
            obj = self.model(**obj_in)
            self.db.add(obj)
            await self.db.flush()   # instead of commit
            await self.db.refresh(obj)
            return obj
        except Exception as e:
            print(e)
            raise RepoException(
                status_code=500,
                detail="Error creating object",
                additional_info={"error": str(e), "data": obj_in}
            )

    async def update(self, id: UUID, obj_in: dict) -> Optional[T]:
        try:
            obj = await self.get(id)
            if not obj:
                return None
            for key, value in obj_in.items():
                setattr(obj, key, value)
            await self.db.flush()   # instead of commit
            await self.db.refresh(obj)
            return obj
        except Exception as e:
            raise RepoException(
                status_code=500,
                detail="Error updating object",
                additional_info={"error": str(e), "id": str(id), "data": obj_in}
            )

    async def delete(self, id: UUID) -> bool:
        try:
            obj = await self.get(id)
            if not obj:
                return False
            await self.db.delete(obj)
            await self.db.flush()   # instead of commit
            return True
        except Exception as e:
            raise RepoException(
                status_code=500,
                detail="Error deleting object",
                additional_info={"error": str(e), "id": str(id)}
            )
