import sys
from typing import Any, Dict, Generic

if sys.version_info < (3, 8):
    from typing_extensions import Protocol  # pragma: no cover
else:
    from typing import Protocol  # pragma: no cover

from library.fastapi_users_verification.models import SMP, SSP, MessageTransport

# class VerificationMessageManager(Protocol, Generic[SSP, SMP]):
#     """Protocol for sending verification message"""
#     session: MessageTransport

#     def __init__(self, session: MessageTransport):
#         self.session = session


#     async def send(self, recver_dict: Dict[str, Any]) -> bool:
#         """Send a verification message"""
        # await self.session.send(recver_dict)
        # ...  # pragma: no cover