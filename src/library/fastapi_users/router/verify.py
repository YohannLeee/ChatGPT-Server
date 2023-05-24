from typing import Type
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import EmailStr

from library.fastapi_users import exceptions, models, schemas
from library.fastapi_users.manager import BaseUserManager, UserManagerDependency
from library.fastapi_users.router.common import ErrorCode, ErrorModel
from library.fastapi_users.message import Message, mk_json_res
from library.fastapi_users.authentication import Authenticator


def get_verify_router(
    get_user_manager: UserManagerDependency[models.UP, models.ID],
    user_schema: Type[schemas.U],
    authenticator: Authenticator,
):
    router = APIRouter()
    get_current_active_user = authenticator.current_user(
        active=True
    )

    @router.post(
        "/request-verify-token",
        status_code=status.HTTP_202_ACCEPTED,
        name="verify:request-token",
        dependencies = [Depends(get_current_active_user)]
    )
    async def request_verify_token(
        request: Request,
        email: EmailStr = Body(..., embed=True),
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ):
        try:
            user = await user_manager.get_by_email(email)
            await user_manager.request_verify(user, request)
        except exceptions.UserNotExists:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail = ErrorCode.USER_NOT_EXIST
            )
        except exceptions.UserInactive:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= ErrorCode.CURRENT_USER_NOT_ACTIVE
            )
        except exceptions.UserAlreadyVerified:
            raise HTTPException(
                status_code= status.HTTP_406_NOT_ACCEPTABLE,
                detail= ErrorCode.VERIFY_USER_ALREADY_VERIFIED
            )

        return mk_json_res(Message.VERIFY_MAIL_SENT)

    @router.post(
        "/verify",
        response_model=user_schema,
        name="verify:verify",
        responses={
            status.HTTP_400_BAD_REQUEST: {
                "model": ErrorModel,
                "content": {
                    "application/json": {
                        "examples": {
                            ErrorCode.VERIFY_USER_BAD_TOKEN[1]: {
                                "summary": "Bad token, not existing user or"
                                "not the e-mail currently set for the user.",
                                "value": mk_json_res(ErrorCode.VERIFY_USER_BAD_TOKEN),
                            },
                            ErrorCode.VERIFY_USER_ALREADY_VERIFIED[1]: {
                                "summary": "The user is already verified.",
                                "value": mk_json_res(ErrorCode.VERIFY_USER_ALREADY_VERIFIED)
                            },
                        }
                    }
                },
            }
        },
    )
    async def verify(
        request: Request,
        token: str = Body(..., embed=True),
        user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    ):
        logging.debug(f"token: {token}")
        try:
            return await user_manager.verify(token, request)
        except (exceptions.InvalidVerifyToken, exceptions.UserNotExists):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.VERIFY_USER_BAD_TOKEN,
            )
        except exceptions.UserAlreadyVerified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.VERIFY_USER_ALREADY_VERIFIED,
            )
        # return {"detail": Message.VERIFY_MAIL_OK}

    return router

    # @router.post(
    #     "/verify",
    #     response_model=user_schema,
    #     name="verify:verify",
    #     responses={
    #         status.HTTP_400_BAD_REQUEST: {
    #             "model": ErrorModel,
    #             "content": {
    #                 "application/json": {
    #                     "examples": {
    #                         ErrorCode.VERIFY_USER_BAD_TOKEN: {
    #                             "summary": "Bad token, not existing user or"
    #                             "not the e-mail currently set for the user.",
    #                             "value": {"detail": ErrorCode.VERIFY_USER_BAD_TOKEN},
    #                         },
    #                         ErrorCode.VERIFY_USER_ALREADY_VERIFIED: {
    #                             "summary": "The user is already verified.",
    #                             "value": {
    #                                 "detail": ErrorCode.VERIFY_USER_ALREADY_VERIFIED
    #                             },
    #                         },
    #                     }
    #                 }
    #             },
    #         }
    #     },
    # )
    # async def verify(
    #     request: Request,
    #     token: str = Body(..., embed=True),
    #     user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    # ):
    #     try:
    #         return await user_manager.verify(token, request)
    #     except (exceptions.InvalidVerifyToken, exceptions.UserNotExists):
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=ErrorCode.VERIFY_USER_BAD_TOKEN,
    #         )
    #     except exceptions.UserAlreadyVerified:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=ErrorCode.VERIFY_USER_ALREADY_VERIFIED,
    #         )

    # return router
