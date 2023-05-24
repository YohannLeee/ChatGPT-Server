from typing import Any, Type
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from library.fastapi_users import exceptions, models, schemas
from library.fastapi_users.authentication import Authenticator
from library.fastapi_users.manager import BaseUserManager, UserManagerDependency
from library.fastapi_users.router.common import ErrorCode, ErrorModel
from library.fastapi_users.message import mk_json_res

log = logging.getLogger('app')

def get_users_router(
    get_user_manager: UserManagerDependency[models.UP, models.ID],
    user_schema: Type[schemas.U],
    user_update_schema: Type[schemas.UU],
    authenticator: Authenticator,
    requires_verification: bool = False,
) -> APIRouter:
    """Generate a router with the authentication routes."""
    router = APIRouter()

    get_current_active_user = authenticator.current_user(
        active=True, verified=requires_verification
    )
    get_current_superuser = authenticator.current_user(
        active=True, verified=requires_verification, superuser=True
    )

    async def get_user_or_404(
        id: Any,
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ) -> models.UP:
        try:
            parsed_id = user_manager.parse_id(id)
            return await user_manager.get(parsed_id)
        except (exceptions.UserNotExists, exceptions.InvalidID) as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from e

    @router.get(
        "/me",
        response_model=user_schema,
        name="users:current_user",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
        },
    )
    async def me(
        user: models.UP = Depends(get_current_active_user),
    ):
        return user_schema.from_orm(user)

    @router.patch(
        "/me",
        response_model=user_schema,
        dependencies=[Depends(get_current_active_user)],
        name="users:patch_current_user",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_400_BAD_REQUEST: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS[1]: {
                                "summary": "A user with this email already exists.",
                                "value": mk_json_res(ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS)
                            },
                            ErrorCode.UPDATE_USER_INVALID_PASSWORD[1]: {
                                "summary": "Password validation failed.",
                                "value": mk_json_res(
                                    ErrorCode.UPDATE_USER_INVALID_PASSWORD, 
                                    {"reason": "Password should be at least 3 characters"}
                                )
                            },
                        }
                    }
                },
            },
        },
    )
    async def update_me(
        request: Request,
        user_update: user_update_schema,  # type: ignore
        user: models.UP = Depends(get_current_active_user),
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ):
        log.debug("Update me")
        try:
            user = await user_manager.update(
                user_update, user, safe=True, request=request
            )
            return user_schema.from_orm(user)
        except exceptions.InvalidPasswordException as e:
            log.error("密码无效")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.UPDATE_USER_INVALID_PASSWORD
            )
        except exceptions.UserAlreadyExists:
            log.error("用户已存在")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS,
            )

    @router.get(
        "/{id}",
        response_model=user_schema,
        dependencies=[Depends(get_current_superuser)],
        name="users:user",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Not a superuser.",
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "The user does not exist.",
            },
        },
    )
    async def get_user(user=Depends(get_user_or_404)):
        return user_schema.from_orm(user)

    @router.patch(
        "/{id}",
        response_model=user_schema,
        dependencies=[Depends(get_current_superuser)],
        name="users:patch_user",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Not a superuser.",
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "The user does not exist.",
            },
            status.HTTP_400_BAD_REQUEST: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS[1]: {
                                "summary": "A user with this email already exists.",
                                "value": mk_json_res(ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS)
                            },
                            ErrorCode.UPDATE_USER_INVALID_PASSWORD[1]: {
                                "summary": "Password validation failed.",
                                "value": mk_json_res(
                                    ErrorCode.UPDATE_USER_INVALID_PASSWORD,
                                    {"reason": "Password should be at least 3 characters"}
                                ),
                            },
                        }
                    }
                },
            },
        },
    )
    async def update_user(
        user_update: user_update_schema,  # type: ignore
        request: Request,
        user=Depends(get_user_or_404),
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ):
        try:
            user = await user_manager.update(
                user_update, user, safe=False, request=request
            )
            return user_schema.from_orm(user)
        except exceptions.InvalidPasswordException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.UPDATE_USER_INVALID_PASSWORD,
            )
        except exceptions.UserAlreadyExists:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS,
            )

    @router.delete(
        "/{id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        dependencies=[Depends(get_current_superuser)],
        name="users:delete_user",
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user.",
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Not a superuser.",
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "The user does not exist.",
            },
        },
    )
    async def delete_user(
        user=Depends(get_user_or_404),
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ):
        await user_manager.delete(user)
        return None

    return router
