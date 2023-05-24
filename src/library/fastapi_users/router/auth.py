from typing import Tuple
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from library.fastapi_users import models, schemas
from library.fastapi_users.authentication import AuthenticationBackend, Authenticator, Strategy
from library.fastapi_users.manager import BaseUserManager, UserManagerDependency
from library.fastapi_users.openapi import OpenAPIResponseType
from library.fastapi_users.router.common import ErrorCode, ErrorModel
from library.fastapi_users.message import mk_json_res

log = logging.getLogger('app')

def get_auth_router(
    backend: AuthenticationBackend,
    get_user_manager: UserManagerDependency[models.UP, models.ID],
    authenticator: Authenticator,
    requires_verification: bool = False,
) -> APIRouter:
    """Generate a router with login/logout routes for an authentication backend."""
    router = APIRouter()
    get_current_user_token = authenticator.current_user_token(
        active=True, verified=requires_verification
    )

    login_responses: OpenAPIResponseType = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.LOGIN_BAD_CREDENTIALS[1]: {
                            "summary": "Bad credentials or the user is inactive.",
                            "value": mk_json_res(ErrorCode.LOGIN_BAD_CREDENTIALS),
                        },
                        ErrorCode.LOGIN_USER_NOT_VERIFIED[1]: {
                            "summary": "The user is not verified.",
                            "value": mk_json_res(ErrorCode.LOGIN_USER_NOT_VERIFIED),
                        },
                    }
                }
            },
        },
        **backend.transport.get_openapi_login_responses_success(),
    }

    @router.post(
        "/login",
        name=f"auth:{backend.name}.login",
        responses=login_responses,
    )
    async def login(
        request: Request,
        response: Response,
        # credentials: OAuth2PasswordRequestForm = Depends(),
        credentials: schemas.UL,
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
        strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    ):
        # log.debug(f"{credentials=}")
        user = await user_manager.authenticate(credentials)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.CURRENT_USER_NOT_ACTIVE,
            )

        if requires_verification and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
            )
        login_return = await backend.login(strategy, user, response)
        await user_manager.on_after_login(user, request)
        return login_return

    logout_responses: OpenAPIResponseType = {
        **{
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user."
            }
        },
        **backend.transport.get_openapi_logout_responses_success(),
    }

    @router.post(
        "/logout", name=f"auth:{backend.name}.logout", responses=logout_responses
    )
    async def logout(
        response: Response,
        user_token: Tuple[models.UP, str] = Depends(get_current_user_token),
        strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    ):
        user, token = user_token
        return await backend.logout(strategy, user, token, response)

    return router
