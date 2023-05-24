import sys
from typing import Any, Generic, Sequence, TypeVar


if sys.version_info < (3, 8):
    from typing_extensions import Protocol  # pragma: no cover
else:
    from typing import Protocol  # pragma: no cover

class MessageTransport(Protocol):
    """Protocol that send a verification message should follow"""

    def __init__(self, *a, **ka) -> None:
        ...  # pragma: no cover

    async def send(self, recver_dict: dict[str, Any]):
        ...  # pragma: no cover




class SMSTransport(MessageTransport):
    """SMS protocol that send a sms shoud follow"""
    body: str
    def __init__(self, *args, **kwargs) -> None:
        ...  # pragma: no cover


# VMP = TypeVar('VMP', bound= VerificationMessageModel)
# SMP = TypeVar("SMP", bound= MailTransport)
# SSP = TypeVar("SSP", bound= SMSTransport)