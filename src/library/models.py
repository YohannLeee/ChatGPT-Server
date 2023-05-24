import sys
from typing import TypeVar



if sys.version_info < (3, 8):
    from typing_extensions import Protocol  # pragma: no cover
else:
    from typing import Protocol  # pragma: no cover

ID = TypeVar("ID")

class QuestionProtocol(Protocol[ID]):
    """Question protocol that ORM model should follow"""
    id: ID
    content: str
    user_id: ID
    approach: int
    usage: int
    ip: str
    timestamp: int

    def __init__(self, *args, **kwargs) -> None:
        ...  # pragma: no cover


class AnwserProtocol(Protocol[ID]):
    """Anwser protocol that ORM model should follow"""
    id: ID
    content: str
    user_id: ID
    question_id: ID
    approach: int
    usage: int
    timestamp: int

    def __init__(self, *args, **kwargs) -> None:
        ...  # pragma: no cover


class ChatProtocol(Protocol[ID]):
    """Chat protocol"""
    id: ID
    name: str
    user_id: ID
    timestamp: int

    def __init__(self, *args, **kwargs) -> None:
        ...  # pragma: no cover

class ApproachProtocol(Protocol[ID]):
    """Approach protocol"""
    id: ID
    name: str
    user_id: ID
    timestamp: int

    def __init__(self, *args, **kwargs) -> None:
        ...  # pragma: no cover

class PageProtocol(Protocol[ID]):
    """Page protocol"""
    id: ID
    url: str
    authed_visit_count: int
    unauthed_visit_count: int

    def __init__(self, *args, **kwargs) -> None:
        ...  # pragma: no cover


class VisitProtocol(Protocol[ID]):
    """Visit protocol"""
    id: ID
    visitor_id: ID
    page_id: ID
    timestamp: int

    def __init__(self, *args, **kwargs) -> None:
        ...  # pragma: no cover


class VisitorProtocol(Protocol[ID]):
    """Visitor protocol"""
    id: ID
    ip: str
    user_agent: str

    def __init__(self, *args, **kwargs) -> None:
        ...  # pragma: no cover


QP = TypeVar("QP", bound=QuestionProtocol)
AP = TypeVar("AP", bound=AnwserProtocol)
CP = TypeVar("CP", bound=ChatProtocol)
ApP = TypeVar("ApP", bound=ApproachProtocol)
PP = TypeVar("PP", bound=PageProtocol)
VP = TypeVar("VP", bound=VisitProtocol)
VtorP = TypeVar("VtorP", bound=VisitorProtocol)