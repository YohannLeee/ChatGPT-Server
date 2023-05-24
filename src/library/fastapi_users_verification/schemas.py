from typing import Sequence, TypeVar
from pydantic import BaseModel


class VerificationMessageModel(BaseModel):
    """Verification token that would be included in message"""
    token: str


class MailAccountModel(BaseModel):
    mail_host: str
    mail_port: int
    mail_user: str
    mail_password: str

class MailModel(BaseModel):
    sender: str
    to_address: Sequence[str]
    subject: str = ""
    body: str = ""

VM = TypeVar("VM", bound=VerificationMessageModel)
MA = TypeVar("MA", bound=MailAccountModel)
M = TypeVar("M", bound=MailModel)