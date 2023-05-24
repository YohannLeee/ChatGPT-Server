from library.fastapi_users.authentication.strategy.base import (
    Strategy,
    StrategyDestroyNotSupportedError,
)
from library.fastapi_users.authentication.strategy.db import (
    AP,
    AccessTokenDatabase,
    AccessTokenProtocol,
    DatabaseStrategy,
)
from library.fastapi_users.authentication.strategy.jwt import JWTStrategy

try:
    from library.fastapi_users.authentication.strategy.redis import RedisStrategy
except ImportError:  # pragma: no cover
    pass

__all__ = [
    "AP",
    "AccessTokenDatabase",
    "AccessTokenProtocol",
    "DatabaseStrategy",
    "JWTStrategy",
    "Strategy",
    "StrategyDestroyNotSupportedError",
    "RedisStrategy",
]
