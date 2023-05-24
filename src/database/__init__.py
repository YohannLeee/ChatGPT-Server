"""
question
- rowid
- question_id
- question
- user_id
- approach
- usage
- timestamp

anwser
- rowid
- id
- content
- user_id
- usage
- timestamp

user_cost_count
- user_id
- anwsers
- questions
- tokens

user_persists
- user_id
- balance
- tokens
"""
from typing import AsyncGenerator

from fastapi import Depends
from library.fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from library.fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID, SQLAlchemyAccessTokenDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from database.question import BaseQuestionTableUUID, BaseQuestionDatabase
from database.anwser import BaseAnwserTableUUID, BaseAnwserDatabase
from database.pages import BasePageTable, BasePageDatabase
from database.approach import BaseApproachTable, BaseApproachDatabase
from database.visits import BaseVisitTableUUID, BasevisitDatabase
from database.visitors import BasevisitorTable, BasevisitorDatabase

# DATABASE_URL = "sqlite+aiosqlite:///./test.db"
DATABASE_URL = "postgresql+asyncpg://yohann:yohann327@localhost/aigc"


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

class Token(SQLAlchemyBaseAccessTokenTableUUID, Base):
    pass

class Question(BaseQuestionTableUUID, Base):
    pass

class Anwser(BaseAnwserTableUUID, Base):
    pass

class Page(BasePageTable, Base):
    pass

class Approach(BaseApproachTable, Base):
    pass

class Visits(BaseVisitTableUUID, Base):
    pass

class Visitors(BasevisitorTable, Base):
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

async def get_question_db(session: AsyncSession = Depends(get_async_session)):
    yield BaseQuestionDatabase(session, Question)

async def get_anwser_db(session: AsyncSession = Depends(get_async_session)):
    yield BaseAnwserDatabase(session, Anwser)

async def get_page_db(session: AsyncSession = Depends(get_async_session)) -> BasePageDatabase:
    yield BasePageDatabase(session, Page)

async def get_approach_db(session: AsyncSession = Depends(get_async_session)):
    yield BaseApproachDatabase(session, Approach)

async def get_visit_db(session: AsyncSession = Depends(get_async_session)):
    yield BasevisitDatabase(session, Visits)

async def get_visitor_db(session: AsyncSession = Depends(get_async_session)):
    yield BasevisitorDatabase(session, Visitors)
