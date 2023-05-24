from typing import Any, Generic, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, Integer, and_
from sqlalchemy.orm import Mapped, mapped_column

from library.fastapi_users.models import ID
from library.models import VtorP

class BasevisitorTable(Generic[ID]):
    """
    Base visitor table
    """
    __tablename__ = "visitor"

    id: Mapped[ID] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    ip: Mapped[str] = mapped_column(String)
    user_agent: Mapped[str] = mapped_column(String)

class BasevisitorDatabase(Generic[ID]):
    """
    Database adapter for SQLAlchemy

    :param session: SQLAlchemy session instance.
    :param table: SQLAlchemy question model.
    """

    session: AsyncSession
    table: Type[VtorP]
    
    def __init__(
        self,
        session: AsyncSession,
        table: Type[VtorP]
    ):
        self.session = session
        self.table = table

    async def create(self, create_dict: dict[str, Any]) -> VtorP:
        visitor = self.table(**create_dict)
        self.session.add(visitor)
        await self.session.commit()
        return visitor

    async def update(self, visitor: VtorP, update_dict: dict[str, Any]) -> VtorP:
        for key, value in update_dict.items():
            setattr(visitor, key, value)
        self.session.add(visitor)
        await self.session.commit()
        return visitor

    async def delete(self, visitor: VtorP) -> None:
        await self.session.delete(visitor)
        await self.session.commit()

    async def get_visitors(self) -> Optional[list[VtorP]]:
        result = await self.session.execute(
            select(self.table)
        )
        return result.scalars().all()

    async def get_visitor(self, visitor: VtorP) -> Optional[VtorP]:
        result = await self.session.execute(
            select(self.table).where(
                and_(visitor.ip == self.table.ip, visitor.user_agent == self.table.user_agent)
            )
        )
        return result.unique().scalar_one_or_none()
