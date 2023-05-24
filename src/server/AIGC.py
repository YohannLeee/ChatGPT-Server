import logging
# import xml.etree.cElementTree as et
import time
# import sys
# import pathlib
# sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())

from fastapi import Depends, Response, Request, status, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from AIGC.ChatGPT import Chatbot
from database import User, get_question_db, BaseQuestionDatabase, get_anwser_db, BaseAnwserDatabase
from library.fastapi_users.message import Message
from library.schemas import BaseQuestion


log = logging.getLogger('app.server')
# app = FastAPI(root_path='/chat')


async def get_chatbot() -> Chatbot:
    yield Chatbot.get_instance()

class UserContent(BaseModel):
    userName: str = 'user1'
    content: str = '你好'
    accessToken: str = 'testToken202304041811'


async def test_stream():
    for i in range(20):
        log.debug(f"yield {i} ")
        time.sleep(0.1)
        yield f"{i} "

def get_aigc_router(current_active_user):

    router = APIRouter()
    @router.post("/ask_stream")
    async def test_chatGPT(
        data: UserContent, 
        chat: Chatbot = Depends(get_chatbot), 
        user: User = Depends(current_active_user),
        request: Request = None,
        question_db: BaseQuestionDatabase = Depends(get_question_db),
        anwser_db: BaseAnwserDatabase = Depends(get_anwser_db)
        ):
        """ChatGPT web service test api
        body: 
            - accessToken: token
            userName: user1
            content: string

        Args:
            request (Request): _description_
            response (Response): _description_
        """
        log.debug(f"data: {data}")
        log.debug(f"chat: {chat}")
        log.debug(f"Received request from {data.userName}")
        log.debug(f"Content: {data.content}")
        log.debug(f"accessToken: {data.accessToken}")
        # create question object
        question_dict = BaseQuestion(
            content= data.content,
            user_id= user.id,
            approach=1,
            usage=0,
            ip = request.client.host,
            timestamp= int(time.time())
        )

        question_dict = await question_db.create(question_dict.dict())
        # log.debug(f"{question_dict=}")

        if not user.is_verified:
            log.error(f"User {user.email} not verified")
            raise HTTPException(
                status_code=403,
                detail=Message.USER_NOT_VERIFIED,
            )
        return StreamingResponse(
            chat.async_ask_stream(
                prompt=data.content,
                question_dict = question_dict,
                anwser_db = anwser_db
            )
        )


    @router.post("/test")
    @router.get("/test")
    async def test_status(request: Request, response: Response):
        """
        Test if server alive
        """
        log.debug(f"testing")
        # content_length = request.headers.get('Content-Length')
        # if content_length and int(content_length) > 0:
        #     body = (await request.body()).decode()
        # else:
        #     body = content_length
        body = (await request.body()).decode()
        params = dict(request.query_params.items())
        response.status_code = status.HTTP_200_OK
        res = {'body': body, 'params': params}
        log.debug(f"{res=}")
        return res
    
    return router