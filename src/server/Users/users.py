import uuid
from typing import Optional, Coroutine, Any
import logging

from fastapi import Depends, Request
from library.fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from library.fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
    CookieTransport
)
from library.fastapi_users.authentication.strategy.db import DatabaseStrategy
from library.fastapi_users.db import SQLAlchemyUserDatabase
from library.fastapi_users import models, schemas, exceptions

from database import User, get_user_db, get_token_db, SQLAlchemyAccessTokenDatabase
from library.fastapi_users_verification.schemas import MailModel
from library.fastapi_users_verification.transport import MailTransport
from server.Users.cfg import REQUEST_VERIFY_BODY, MAIL_ACCOUNT

log = logging.getLogger('app')
SECRET = "SECRET"

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        log.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        log.info(f"User {user.id} has forgot their password. Reset token: {token}")
        reset_pwd_path = '/auth/reset-password'
        log.debug(f"{request.headers=}")
        url = f"{request.base_url.scheme}://{request.base_url.netloc}{reset_pwd_path}?token={token}"
        log.info(f"Verification requested for user {user.id}. Verification token: {token}")
        verificator: MailTransport = MailTransport(account= MAIL_ACCOUNT)
        await verificator.send(MailModel(
            sender = 'zhiyuanai001@163.com',
            to_address= [user.email],
            subject='智远AI找回密码通知',
            body=REQUEST_VERIFY_BODY % {'mail': user.email, 'verify_url': url}
            )
        )

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None, 
    ):
        # log.debug(f"{request.url=}")
        # log.debug(f"{request.base_url=}")
        verify_path = '/auth/verify'
        verify_url = f"{request.base_url.scheme}://{request.base_url.netloc}{verify_path}?token={token}"
        log.info(f"Verification requested for user {user.id}. Verification token: {token}")
        verificator: MailTransport = MailTransport(account= MAIL_ACCOUNT)
        await verificator.send(MailModel(
            sender = 'zhiyuanai001@163.com',
            to_address= [user.email],
            subject='智远AI邮箱验证通知',
            body=REQUEST_VERIFY_BODY % {'mail': user.email, 'verify_url': verify_url}
            )
        )


    async def on_after_verify(self, user: models.UP, request: Optional[Request] = None) -> None:
        log.info(f"User {user.id} has successfully verified")
        return await super().on_after_verify(user, request)

    async def validate_password(self, password: str, user: schemas.UC| models.UP) -> Coroutine[Any, Any, None]:
        """
        密码必须6-20位
        """
        if not 6 <= len(password) <= 20:
            raise exceptions.InvalidPasswordException(
                reason="密码必须6~20位"
            )
        return await super().validate_password(password, user)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
cookie_transport = CookieTransport(cookie_max_age=3600*8, cookie_secure= False)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

def get_db_strategy(database: SQLAlchemyAccessTokenDatabase = Depends(get_token_db)) -> DatabaseStrategy:
    return DatabaseStrategy(database, lifetime_seconds= 3600)


bearer_jwt_backend = AuthenticationBackend(
    name="bearer+jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

cookie_db_backend = AuthenticationBackend(
    name = 'cookie+db',
    transport=cookie_transport,
    get_strategy=get_db_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [cookie_db_backend])

current_active_user = fastapi_users.current_user(active=True)
