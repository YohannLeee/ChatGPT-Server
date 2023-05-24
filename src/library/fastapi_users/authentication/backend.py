from typing import Any, Generic
import logging

from fastapi import Response

from library.fastapi_users import models
from library.fastapi_users.authentication.strategy import (
    Strategy,
    StrategyDestroyNotSupportedError,
)
from library.fastapi_users.authentication.transport import (
    Transport,
    TransportLogoutNotSupportedError,
)
from library.fastapi_users.types import DependencyCallable

log = logging.getLogger('app')

class AuthenticationBackend(Generic[models.UP, models.ID]):
    """
    Combination of an authentication transport and strategy.

    Together, they provide a full authentication method logic.

    :param name: Name of the backend.
    :param transport: Authentication transport instance.
    :param get_strategy: Dependency callable returning
    an authentication strategy instance.
    """

    name: str
    transport: Transport

    def __init__(
        self,
        name: str,
        transport: Transport,
        get_strategy: DependencyCallable[Strategy[models.UP, models.ID]],
    ):
        self.name = name
        self.transport = transport
        self.get_strategy = get_strategy

    async def login(
        self,
        strategy: Strategy[models.UP, models.ID],
        user: models.UP,
        response: Response,
    ) -> Any:
        token = await strategy.write_token(user)
        return await self.transport.get_login_response(token, response)

    async def logout(
        self,
        strategy: Strategy[models.UP, models.ID],
        user: models.UP,
        token: str,
        response: Response,
    ) -> Any:
        try:
            await strategy.destroy_token(token, user)
            log.debug(f"用户{user.email} 已退出")
        except StrategyDestroyNotSupportedError:
            pass

        try:
            return await self.transport.get_logout_response(response)
        except TransportLogoutNotSupportedError:
            return None
