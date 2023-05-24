import time
from typing import Any, Generic, Optional, Type
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from library.fastapi_users.models import ID
from library.models import VP

UUID_ID = uuid.UUID

class BaseVisitTable(Generic[ID]):
    """
    Base visit table
    """
    __tablename__ = "visit"

    id: Mapped[ID] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    visitor_id: Mapped[ID] = mapped_column(Integer)
    page_id: Mapped[ID] = mapped_column(Integer)
    timestamp: Mapped[int] = mapped_column(Integer, default=int(time.time()))

class BaseVisitTableUUID(BaseVisitTable[UUID_ID]):
    visitor_id: Mapped[UUID_ID] = mapped_column(
        UUID(as_uuid=True)
    )

class BasevisitDatabase(Generic[ID]):
    """
    Database adapter for SQLAlchemy

    :param session: SQLAlchemy session instance.
    :param table: SQLAlchemy question model.
    """

    session: AsyncSession
    table: Type[VP]
    
    def __init__(
        self,
        session: AsyncSession,
        table: Type[VP]
    ):
        self.session = session
        self.table = table

    async def create(self, create_dict: dict[str, Any]) -> VP:
        visit = self.table(**create_dict)
        self.session.add(visit)
        await self.session.commit()
        return visit

    async def update(self, visit: VP, update_dict: dict[str, Any]) -> VP:
        for key, value in update_dict.items():
            setattr(visit, key, value)
        self.session.add(visit)
        await self.session.commit()
        return visit

    async def delete(self, visit: VP) -> None:
        await self.session.delete(visit)
        await self.session.commit()

    async def get_visits(self) -> Optional[list[VP]]:
        result = await self.session.execute(
            select(self.table)
        )
        return result.scalars().all()