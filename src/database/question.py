import time
from typing import Any, Generic, Optional, Type
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select, select, Column, String, Integer, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from library.fastapi_users.models import ID, UP
from library.models import QP

UUID_ID = uuid.UUID

class BaseQuestionTable(Generic[ID]):
    """
    Base question table
    """
    __tablename__ = "question"

    id: Mapped[ID] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(String)
    user_id: Mapped[ID] = mapped_column(String(36))
    approach: Mapped[int] = mapped_column(Integer)
    usage: Mapped[int] = mapped_column(Integer)
    ip: Mapped[str] = mapped_column(String)
    timestamp: Mapped[int] = mapped_column(Integer)

class BaseQuestionTableUUID(BaseQuestionTable[UUID_ID]):
    # id: Mapped[UUID_ID] = mapped_column(
    #     String(36), primary_key= True, default=str(uuid.uuid4())
    # )
    id: Mapped[UUID_ID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default= uuid.uuid4, unique=True, nullable=False
    )
    user_id: Mapped[UUID_ID] = mapped_column(UUID(as_uuid=True))


class BaseQuestionDatabase(Generic[ID]):
    """
    Database adapter for SQLAlchemy

    :param session: SQLAlchemy session instance.
    :param table: SQLAlchemy question model.
    """

    session: AsyncSession
    table: Type[QP]
    
    def __init__(
        self,
        session: AsyncSession,
        table: Type[QP]
    ):
        self.session = session
        self.table = table

    async def get_by_id(self, id: ID) -> Optional[QP]:
        statement = select(self.table).where(self.table.id == id)
        return await self._get_question(statement)

    async def get_latest_n(self, user: UP, num: int) -> Optional[list[QP]]:
        statement = select(self.table).where(self.table.user_id == user.id).order_by(self.table.timestamp.desc()).limit(num)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(self, create_dict: dict[str, Any]) -> QP:
        question = self.table(**create_dict)
        self.session.add(question)
        await self.session.commit()
        return question

    async def update(self, question: QP, update_dict: dict[str, Any]) -> QP:
        for key, value in update_dict.items():
            setattr(question, key, value)
        self.session.add(question)
        await self.session.commit()
        return question

    async def delete(self, question: QP) -> None:
        await self.session.delete(question)
        await self.session.commit()
    
    async def _get_question(self, statement: Select) -> Optional[QP]:
        result = await self.session.execute(statement)
        return result.unique().scalar_one_or_none()
