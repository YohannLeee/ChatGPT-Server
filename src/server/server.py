import logging
import json

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uvicorn

from database import User, create_db_and_tables
from server.Users.schemas import UserCreate, UserRead, UserUpdate
from server.Users.users import bearer_jwt_backend, cookie_db_backend, current_active_user, fastapi_users
from server.AIGC import get_aigc_router 
from server.WeCom import router as wecom_router
# from server.visit import get_visit_router
from settings.log import get_log_config
from library.utils import CFG
from library.fastapi_users.message import mk_json_res

log = logging.getLogger('app')
print(log.handlers)

app = FastAPI(
    root_path='/api/'
    )

app.include_router(
    fastapi_users.get_auth_router(bearer_jwt_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_auth_router(cookie_db_backend), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

# app.include_router(
#     fastapi_users.get_oauth_router(),
#     prefix="/oauth",
#     tags = ["auth"]
# )
# app.include_router(
#     fastapi_users.get_oauth_associate_router(),
#     prefix="/oauth",
#     tags = ["auth"]
# )
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

app.include_router(
    get_aigc_router(current_active_user),
    dependencies=[Depends(current_active_user)],
    prefix = "/aigc",
    tags = ["aigc"]
)

app.include_router(
    wecom_router,
    # dependencies=[Depends(current_active_user)],
    prefix = "/wecom",
    tags = ["wecom"]
)

# app.include_router(
#     get_visit_router,
#     prefix="/visit",
#     tags = ["visit"]
# )

@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}

@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()

#@app.middleware("http")
async def log_requests(request: Request, call_next):
    form = await request.form()
    requestions = dict(
        host= request.client.host,
        method = request.method,
        url = request.url.__str__(),
        headers = dict(request.headers.items()),
        params = dict(request.query_params.items()),
        body = (await request.body()).decode(),
        form = dict((await request.form()).items()),
        # json = await request.json()
    )

    # 记录请求数据
    # log.debug(f"Request received: {request.client.host} {request.method} {request.url}")
    # log.debug(f"{request.query_params=}")
    # log.debug(f"Body: {await request.body()}")
    # log.debug(f"Body: {await request.body()}")
    log.debug(f"Received request: {json.dumps(requestions, indent=2)}")

    response = await call_next(request)

    return response


@app.exception_handler(HTTPException)
async def exception_w_code(request, exc: HTTPException):
    res = JSONResponse(
        status_code=exc.status_code,
        content = jsonable_encoder(mk_json_res(exc.detail))
    )
    if exc.headers:
        res.headers = exc.headers
    return res

@app.post("/test")
@app.get("/test")
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
    

async def run_server(port:int  = 0):
    config = uvicorn.Config(
        app = app,
        host=CFG.C['SERVER']['IP'],
        # port=8004,
        port=port or CFG.C['SERVER']['PORT'],
        log_level="debug", 
        log_config=get_log_config()
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        uvicorn.run("app.app:app", host="0.0.0.0", port=8003, log_level="debug", log_config=get_log_config())
    except Exception as e:
        logging.exception(e)
