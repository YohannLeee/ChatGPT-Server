from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import EmailStr

from library.fastapi_users import exceptions, models
from library.fastapi_users.manager import BaseUserManager, UserManagerDependency
from library.fastapi_users.openapi import OpenAPIResponseType
from library.fastapi_users.router.common import ErrorCode, ErrorModel
from library.fastapi_users.message import Message, mk_json_res

RESET_PASSWORD_RESPONSES: OpenAPIResponseType = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorModel,
        "content": {
            "application/json": {
                "examples": {
                    ErrorCode.RESET_PASSWORD_BAD_TOKEN[1]: {
                        "summary": "Bad or expired token.",
                        "value": mk_json_res(ErrorCode.RESET_PASSWORD_BAD_TOKEN),
                    },
                    ErrorCode.RESET_PASSWORD_INVALID_PASSWORD[1]: {
                        "summary": "Password validation failed.",
                        "value": mk_json_res(ErrorCode.RESET_PASSWORD_INVALID_PASSWORD)
                    },
                }
            }
        },
    },
}


def get_reset_password_router(
    get_user_manager: UserManagerDependency[models.UP, models.ID],
) -> APIRouter:
    """Generate a router with the reset password routes."""
    router = APIRouter()

    @router.post(
        "/forgot-password",
        status_code=status.HTTP_202_ACCEPTED,
        name="reset:forgot_password",
    )
    async def forgot_password(
        request: Request,
        email: EmailStr = Body(..., embed=True),
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ):
        try:
            user = await user_manager.get_by_email(email)
        except exceptions.UserNotExists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.FORGOT_PASSWORD_INVALID_EMAIL
            )

        try:
            await user_manager.forgot_password(user, request)
        except exceptions.UserInactive:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.CURRENT_USER_NOT_ACTIVE
            )

        return mk_json_res(Message.VERIFY_MAIL_SENT)

    @router.post(
        "/reset-password",
        name="reset:reset_password",
        responses=RESET_PASSWORD_RESPONSES,
    )
    async def reset_password(
        request: Request,
        token: str = Body(...),
        password: str = Body(...),
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ):
        try:
            await user_manager.reset_password(token, password, request)
        except (
            exceptions.InvalidResetPasswordToken,
            exceptions.UserNotExists,
            exceptions.UserInactive,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.RESET_PASSWORD_BAD_TOKEN,
            )
        except exceptions.InvalidPasswordException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mk_json_res(ErrorCode.RESET_PASSWORD_INVALID_PASSWORD, {"reason": e.reason})
            )
        return mk_json_res(Message.RESET_PASSWORD_OK)

    return router
