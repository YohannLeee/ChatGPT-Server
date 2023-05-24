from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

from library.models import ID



class BaseQuestion(BaseModel, Generic[ID]):
    id: Optional[ID]
    content: str
    user_id: ID
    approach: int
    usage: int
    ip: str
    timestamp: Optional[int]

    class Config:
        orm_mode = True


class BaseAnwser(BaseModel, Generic[ID]):
    id: Optional[ID]
    content: str
    user_id: ID
    question_id: ID
    approach: int
    usage: int
    timestamp: Optional[int]

    class Config:
        orm_mode = True

class BaseChat(BaseModel, Generic[ID]):
    id: Optional[ID]
    name: str
    user_id: ID
    timestamp: Optional[int]

    class Config:
        orm_mode = True


class BaseApproach(BaseModel, Generic[ID]):
    id: Optional[ID]
    name: str
    remark: Optional[str]

class BasePage(BaseModel, Generic[ID]):
    id: ID
    url: str
    authed_visit_count: int
    unauthed_visit_count: int

class CreatePage(BasePage):
    id: Optional[ID]
    url: str
    authed_visit_count: int = 0
    unauthed_visit_count: int = 0

class UpdatePage(BasePage):
    id: Optional[ID]
    url: Optional[str]
    authed_visit_count: Optional[int]
    unauthed_visit_count: Optional[int]

class BaseVisitor(BaseModel, Generic[ID]):
    id: Optional[ID]
    ip: str
    user_agent: str

class AuthedVisitor(BaseVisitor):
    id: ID
    user_agent: Optional[str]

class BaseVisit(BaseModel, Generic[ID]):
    id: ID
    visitor_id: ID
    page_id: ID
    timestamp: int

class CreateVisit(BaseVisit):
    timestamp: Optional[int]
    

Q = TypeVar("Q", bound=BaseQuestion)
A = TypeVar("A", bound=BaseAnwser)
C = TypeVar("C", bound=BaseChat)
BP = TypeVar("BP", bound=BasePage)
CP = TypeVar("CP", bound=CreatePage)
UP = TypeVar("UP", bound=UpdatePage)
BV = TypeVar("BV", bound=BaseVisitor)