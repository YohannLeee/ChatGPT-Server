import json
import logging
from datetime import datetime as dt
import pathlib

import requests


from library.utils import CFG

log = logging.getLogger('app.wcom.msg')

def send_text_to_app(content: str, recvd_cont_dict: dict):
    """send text to WeCom app

    Args:
        content (str): text
        recvd_cont_dict (dict): dict: {ToUserName, FromUserName, CreateTime, MsgType, Content, MsgId, AgentID}
    """
    token = get_access_token()
    url = CFG.C['WeCom']['URL']['SEND_MSG'] % token
    body = {
        'agent_id': ''
    }
    payload = json.dumps({
        "touser": recvd_cont_dict['FromUserName'],
        #    "toparty": config.toparty,
        #    "totag": config.totag,
        "msgtype": "text",
        "agentid": recvd_cont_dict['AgentID'],
        "text": {
            "content": content
        },
        "safe": 0,
        "enable_id_trans": 0,
        "enable_duplicate_check": 0
    })
    res = requests.post(url, data=payload)
    log.debug(f"Status: {res.status_code}")

def get_access_token():
    token_file = pathlib.Path(CFG.C['WeCom']['ACCESS_TOKEN_CACHE']).expanduser()
    if token_file.exists():
        with open(token_file, 'r') as f:
            token_obj = json.load(f)
        if token_valid(token_obj):
            return token_obj['token']
    url = CFG.C['WeCom']['URL']['ACCTK'] % (CFG.C['WeCom']['CorpID'], CFG.C['WeCom']['Secret'])
    res = requests.get(url, verify=False)
    log.debug(f"status: {res.status_code}")
    access_token = res.json()['access_token']
    store_token(access_token)
    return access_token

def store_token(token: str):
    token_file = pathlib.Path(CFG.C['WeCom']['ACCESS_TOKEN_CACHE']).expanduser()
    # 企业微信设置token 7200s 过期，但是也可能提前过期，所以认为缩短200s
    token_obj = {'token': token, 'expiry': int(dt.timestamp(dt.now())) + 7000 }
    with open(token_file, 'w') as f:
        json.dump(token_obj, f)

def token_valid(token_obj: dict) -> bool:
    if int(token_obj['expiry']) < dt.timestamp(dt.now()):
        log.warning(f"Token expired, will request new token")
        return False
    log.debug(f"Get valid cache token")
    return True

