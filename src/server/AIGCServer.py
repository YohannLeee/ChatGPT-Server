import logging
import asyncio

from fastapi import FastAPI
import uvicorn

from settings import conf

log = logging.getLogger('app.server')
app = FastAPI()

@app.post('/recvWeComMsg')
@app.get('/recvWeComMsg')
def recvWeComMsg():
    log.debug('routing to recvWeComMsg')
    return {'message': 'Hello WeCom'}


def run_server():
    log.debug("Running server")
    uvicorn.run(app, port=conf.SERVER_PORT, )


if __name__ == '__main__':
    run_server()