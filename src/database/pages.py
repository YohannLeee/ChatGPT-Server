from typing import Any, Generic, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from library.fastapi_users.models import ID
from library.models import PP
from library.schemas import BP

class BasePageTable(Generic[ID]):
    """
    Base page table
    """
    __tablename__ = "page"

    id: Mapped[ID] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String)
    authed_visit_count: Mapped[int] = mapped_column(Integer)
    unauthed_visit_count: Mapped[int] = mapped_column(Integer)

class BasePageDatabase(Generic[ID]):
    """
    Database adapter for SQLAlchemy

    :param session: SQLAlchemy session instance.
    :param table: SQLAlchemy question model.
    """

    session: AsyncSession
    table: Type[PP]
    
    def __init__(
        self,
        session: AsyncSession,
        table: Type[PP]
    ):
        self.session = session
        self.table = table

    async def create(self, create_dict: dict[str, Any]) -> PP:
        page = self.table(**create_dict)
        self.session.add(page)
        await self.session.commit()
        return page

    async def update(self, page: PP, update_dict: Optional[dict[str, Any]] = None) -> PP:
        for key, value in update_dict.items():
            setattr(page, key, value)
        self.session.add(page)
        await self.session.commit()
        return page

    async def delete(self, page: PP) -> None:
        await self.session.delete(page)
        await self.session.commit()

    async def get_page_by_id(self, id: int) -> PP:
        result = await self.session.execute(
            select(self.table).where(self.table.id == id)
        )
        return result.unique().scalar_one_or_none()

    async def get_page_by_url(self, url: str) -> PP:
        result = await self.session.execute(
            select(self.table).where(self.table.url == url)
        )
        return result.unique().scalar_one_or_none()
    
    async def get_pages(self) -> Optional[list[PP]]:
        result = await self.session.execute(
            select(self.table)
        )
        return result.scalars().all()
