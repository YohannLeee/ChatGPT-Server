import time
from typing import Any, Generic, Optional, Type
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import TIMESTAMP, Select, select, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from library.fastapi_users.models import ID, UP
from library.models import AP

UUID_ID = uuid.UUID

class BaseAnwserTable(Generic[ID]):
    """
    Base anwser table
    """
    __tablename__ = "anwser"

    id: Mapped[ID] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(String)
    user_id: Mapped[ID] = mapped_column(String(36))
    question_id: Mapped[ID] = mapped_column(String(36))
    approach: Mapped[int] = mapped_column(Integer)
    usage: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[int] = mapped_column(Integer)


class BaseAnwserTableUUID(BaseAnwserTable[UUID_ID]):
    id: Mapped[UUID_ID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default= uuid.uuid4, unique=True, nullable=False
    )
    user_id: Mapped[UUID_ID] = mapped_column(UUID(as_uuid=True))
    question_id: Mapped[UUID_ID] = mapped_column(UUID(as_uuid=True))


class BaseAnwserDatabase(Generic[ID]):
    """
    Database adapter for SQLAlchemy

    :param session: SQLAlchemy session instance.
    :param table: SQLAlchemy anwser model.
    """
    session: AsyncSession
    table: Type[AP]

    def __init__(
        self,
        session: AsyncSession,
        table: Type[AP]
    ):
        self.session = session
        self.table = table

    async def get_by_id(self, id: ID) -> Optional[AP]:
        statement = select(self.table).where(self.table.id == id)
        return await self._get_anwser(statement)

    async def get_latest_n(self, user: UP, num: int) -> Optional[list[AP]]:
        statement = select(self.table).where(self.table.user_id == user.id).order_by(self.table.timestamp.desc()).limit(num)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(self, create_dict: dict[str, Any]) -> AP:
        anwser = self.table(**create_dict)
        self.session.add(anwser)
        await self.session.commit()
        return anwser

    async def update(self, anwser: AP, update_dict: dict[str, Any]) -> AP:
        for key, value in update_dict.items():
            setattr(anwser, key, value)
        self.session.add(anwser)
        await self.session.commit()
        return anwser

    async def delete(self, anwser: AP) -> None:
        await self.session.delete(anwser)
        await self.session.commit()
    
    async def _get_anwser(self, statement: Select) -> Optional[AP]:
        result = await self.session.execute(statement)
        return result.unique().scalar_one_or_none()
