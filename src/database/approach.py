from typing import Any, Generic, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from library.fastapi_users.models import ID
from library.models import ApP

class BaseApproachTable(Generic[ID]):
    """
    Base question table
    """
    __tablename__ = "approach"

    id: Mapped[ID] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String)

class BaseApproachDatabase(Generic[ID]):
    """
    Database adapter for SQLAlchemy

    :param session: SQLAlchemy session instance.
    :param table: SQLAlchemy question model.
    """

    session: AsyncSession
    table: Type[ApP]
    
    def __init__(
        self,
        session: AsyncSession,
        table: Type[ApP]
    ):
        self.session = session
        self.table = table

    async def create(self, create_dict: dict[str, Any]) -> ApP:
        approach = self.table(**create_dict)
        self.session.add(approach)
        await self.session.commit()
        return approach

    async def update(self, approach: ApP, update_dict: dict[str, Any]) -> ApP:
        for key, value in update_dict.items():
            setattr(approach, key, value)
        self.session.add(approach)
        await self.session.commit()
        return approach

    async def delete(self, approach: ApP) -> None:
        await self.session.delete(approach)
        await self.session.commit()

    async def get_approach_by_id(self, id: int) -> ApP:
        result = await self.session.execute(
            select(self.table).where(self.table.id == id)
        )
        return result.unique().scalar_one_or_none()