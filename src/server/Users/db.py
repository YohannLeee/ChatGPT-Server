from typing import AsyncGenerator

from fastapi import Depends
from library.fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from library.fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID, SQLAlchemyAccessTokenDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# DATABASE_URL = "sqlite+aiosqlite:///./test.db"
DATABASE_URL = "postgresql+asyncpg://yohann:yohann327@localhost/aigc"


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

class Token(SQLAlchemyBaseAccessTokenTableUUID, Base):
    pass


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

async def get_token_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyAccessTokenDatabase(session, Token)
