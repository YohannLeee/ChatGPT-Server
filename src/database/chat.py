import time
from typing import Any, Generic, Optional, Type
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select, select, String, Integer, Result
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from library.fastapi_users.models import ID, UP
from library.models import CP

UUID_ID = uuid.UUID

class BaseChatTable(Generic[ID]):
    """
    Base anwser table
    """
    __tablename__ = "chat"

    id: Mapped[ID] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    user_id: Mapped[ID] = mapped_column(String(36))
    timestamp: Mapped[int] = mapped_column(Integer, default=int(time.time()))


class BaseChatTableUUID(BaseChatTable[UUID_ID]):
    id: Mapped[UUID_ID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default= uuid.uuid4, unique=True, nullable=False
    )
    user_id: Mapped[UUID_ID] = mapped_column(UUID(as_uuid=True))


class BaseChatDatabse(Generic[ID]):
    """
    Database adapter for SQLAlchemy

    :param session: SQLAlchemy session instance.
    :param table: SQLAlchemy chat model.
    """
    session: AsyncSession
    table: Type[CP]
    
    def __init__(
        self,
        session: AsyncSession,
        table: Type[CP]
    ):
        self.session = session
        self.table = table

    async def get_chat_by_id(self, id: ID) -> Optional[CP]:
        statement = select(self.table).where(self.table.id == id)
        return await self._get_chat(statement)

    async def get_chat_by_user(self, user: UP) -> Optional[list[CP]]:
        """Get all chats of the user"""
        statement = select(self.table).where(self.table.user_id == user.id).order_by(self.table.timestamp.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(self, create_dict: dict[str, Any]) -> CP:
        chat = self.table(**create_dict)
        self.session.add(chat)
        await self.session.commit()
        return chat

    async def update(self, chat: CP, update_dict: dict[str, Any]) -> CP:
        for key, value in update_dict.items():
            setattr(chat, key, value)
        self.session.add(chat)
        await self.session.commit()
        return chat

    async def delete(self, chat: CP) -> None:
        await self.session.delete(chat)
        await self.session.commit()

    async def _get_chat(self, statement: Select) -> Optional[CP]:
        result = await self.session.execute(statement)
        return result.unique().scalar_one_or_none()