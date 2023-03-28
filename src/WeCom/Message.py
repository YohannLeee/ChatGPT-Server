import json
import logging
from datetime import datetime as dt
import os
import pathlib
import sys
sys.path.append(
    pathlib.Path(__file__).parent.parent.as_posix()
)

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

def get_access_token() -> str:
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

def get_mediar_cache_fp(fn: str = '', suffix: str = '.amr') -> pathlib.Path:
    cache_dir = pathlib.Path(CFG.C['WeCom']['MEDIA_CACHE_DIR']).expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not fn:
        fn = dt.strftime(dt.now(), f"%Y%m%d_%H%M%S{suffix}")
    else:
        fn = f"{fn}{suffix}"
    log.debug(f"Temp media file name: {fn}")
    return cache_dir/fn

def download_temp_media(media_id: str, access_token: str = get_access_token(), fn: str = '') -> str:
    """
    获取临时素材
    Method: GET

    fn: file name,来源于 voice msgid
    """
    url = 'https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token=%s&media_id=%s' % (access_token, media_id)
    res = requests.get(url, verify=False)
    log.debug(f"{res.status_code=}, {res.headers=}")
    if res.status_code == 200:
        fp = get_mediar_cache_fp(fn = fn)
        fp.write_bytes(res.content)
        return fp.as_posix()
    log.error(f"{res.text=}")
    return ''

def download_high_definition_voice_material(media_id: str, access_token: str = get_access_token()) -> str:
    url = 'https://qyapi.weixin.qq.com/cgi-bin/media/get/jssdk?access_token=%s&media_id=%s' % (access_token, media_id)
    res = requests.get(url, verify=False)
    log.debug(f"{res.status_code=}, {res.headers=}")
    if res.status_code == 200:
        fp = get_mediar_cache_fp()
        fp.write_bytes(res.content)
        return fp.as_posix()
    log.error(f"{res.text=}")
    return ''

def amr2pcm(amr_fp: str, wav_fp: str, audio_rate: int = 16000) -> int:
    """
    amr格式语音数据转换为wav格式音频文件
    wav格式的音频文件编码格式为pcm
    """
    return os.system(f'ffmpeg -y -i {amr_fp} -acodec pcm_s16le -ar {audio_rate} {wav_fp}')

def main():
    access_token = get_access_token()
    media_id = '1L4EXHrvnZbZ5Qw5MwD3OpxCLseJkKF0l3juHqlsF1TFTMf-S3CxDx3LdPlcsLHv4'
    download_high_definition_voice_material(access_token, media_id)
    pass


if __name__ == '__main__':
    main()