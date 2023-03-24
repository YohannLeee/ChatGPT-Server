import json
import logging
import asyncio
import hashlib
from base64 import b64decode
import xml.etree.cElementTree as et

from fastapi import FastAPI, Response, Request, status
import uvicorn
from Crypto.Cipher import AES

from settings import conf
from server.utils import aget, XMLParse
from library.utils import CFG
from library.db import DB
from library.WeCom.WXBizMsgCrypt3 import WXBizMsgCrypt as WeComCrypt

log = logging.getLogger('app.server')
app = FastAPI()


def msg_valid(signature: str, *args) -> bool:
    """Check if msg is valid

    Args:
        signature (str): msg_signature

    Returns:
        bool: True valid, False invalid
    """
    log.debug(args)
    sorted_str = ''.join(sorted(args))
    sha1 = hashlib.sha1()
    sha1.update(sorted_str.encode('utf8'))
    _signature = sha1.hexdigest()
    # log.debug(f"{signature=}, {_signature=}")
    return signature == _signature


def format_b64text(b64text: str) -> str:
    len_remain = 4 - (len(b64text) % 4)
    if len_remain == 4:
        return b64text
    else:
        return f"{b64text}{'='*len_remain}"
    

def msg_b64_decrypt(encryped_text_b64: str, encoding_aes_key: str) -> dict:
    """msg decrypt


    Args:
        encryped_text_b64 (str): msg encrypted w/ aes key and then b64encoded
        encoding_aes_key (str): b64 encoding aes key

    Returns:
        str: AES-256-CBC decrypted msg
    """
    encrypted_text = b64decode(encryped_text_b64)
    aes_key = b64decode(format_b64text(encoding_aes_key))
    iv = aes_key[:16]
    # log.debug(f"{aes_key=}, {iv=}")

    # decrypt
    decr = AES.new(aes_key, AES.MODE_CBC, iv)
    msg_bytes = decr.decrypt(encrypted_text)
    # log.debug(f"Decrypted msg: {msg_bytes.decode()}")

    _random = msg_bytes[:16].decode()
    msg_len = int.from_bytes(msg_bytes[16:20], byteorder='big', signed=False)
    msg = msg_bytes[20: 20+msg_len]
    receiveid = msg_bytes[20+msg_len:].decode()
    result = dict(random = _random, length = msg_len, message = msg, receiveid = receiveid)
    # log.debug(f"{result=}")
    return result

# def msg_encrypt_b64(reply_msg: str, timestamp: str, nonce: str, )

# 验证企业微信的URL有效性
@app.get('/recvWeComMsg')
async def recvWeComMsg(request: Request, response: Response):
    log.debug('routing to recvWeComMsg')
    query_params = request.query_params
    signature = query_params.get('msg_signature', '')
    timestamp = query_params.get('timestamp', '')
    nonce = query_params.get('nonce', '')
    echostr = query_params.get('echostr', '')
    log.debug(f"{signature=}, {timestamp=}, {nonce=}, {echostr=}")   

    # 将加密后的字符串与 signature 进行比对
    if msg_valid(signature, CFG.C['WeCom']['Token'], timestamp, nonce, echostr):
        log.debug(f"msg valid")
        msg_dict = msg_b64_decrypt(echostr, CFG.C['WeCom']['EncodingAESKey'])

        response.status_code = status.HTTP_200_OK
        return int(msg_dict['message'])
    else:
        response.status_code = status.HTTP_403_FORBIDDEN
        log.warning("Invalid signature")
        return "Invalid signature"
    
def reply_msg(msg: str):
    return f"您刚刚发送消息: {msg}"
    
@app.post('/recvWeComMsg')
async def post_recvWeComMsg(request: Request, response: Response):
    """接收企业微信用户发送给智远机器人的消息，并且设置回调函数
    企业微信用户发送消息时
    该接口接收到的消息包含2处
        1. url/path?msg_signature=x&timestamp=x&nonce=x
        2. xml text body : <xml> 
                               <ToUserName><![CDATA[toUser]]></ToUserName>
                               <AgentID><![CDATA[toAgentID]]></AgentID>
                               <Encrypt><![CDATA[msg_encrypt]]></Encrypt>
                           </xml>
            其中 msg_encrypt 是加密+b64编码后的一个字符串，格式为
                随机数(16) + 消息长度(4) + 消息文本(x) + 企业ID
            消息文本是一个 xml string
                            <xml>
                                <ToUserName><![CDATA[toUser]]></ToUserName>
                                <FromUserName><![CDATA[fromUser]]></FromUserName>
                                <CreateTime>timestamp</CreateTime>
                                <MsgType><![CDATA[text]]></MsgType>
                                <Content><![CDATA[content]]></Content>
                                <MsgId>msgID</MsgId>
                                <AgentID>agentID</AgentID>
                            </xml>

    收到请求后需要做的步骤:
        1. 验证签名 signature
        2. 转换 xml text body 为 recvd_body dict
        3. 解密解码 msg_encrypt 为 recvd_xml_msg
        4. 转换 recvd_xml_msg 为 recvd_msg_dict
        5. 转换 recvd_msg_dict 中的消息文本为 recvd_cont_dict
        ========== 下面准备好待回复的消息，然后按顺序逆向操作 ========
        
        5. 生成准备回复的文本消息 rply_cont
        6. 填充到 recvd_cont_dict 生成 rply_cont_dict 并转换成 rply_cont_xml
        7. 利用企业微信提供的加密包进行加密、签名、编码
        8. 发送消息

    Args:
        request (Request): _description_
        response (Response): _description_

    Returns:
        _type_: Anything
    """
    body = await request.body()
    xml_parse = XMLParse()
    recvd_body: dict = xml_parse.extract_msg(body)
    log.debug(f"Request body {recvd_body=}")
    
    query_params = request.query_params
    signature = query_params.get('msg_signature', '')
    timestamp = query_params.get('timestamp', '')
    nonce = query_params.get('nonce', '')
    # log.debug(f"{to_user_name=}, {agent_id=}, {encrypt=}")

    if msg_valid(signature, CFG.C['WeCom']['Token'], timestamp, nonce, recvd_body['Encrypt']):
        # encrypt 部分 解密后的dict
        recvd_msg_dict = msg_b64_decrypt(recvd_body['Encrypt'], CFG.C['WeCom']['EncodingAESKey']) # type: ignore
        # 提取 msg_dict 中的内容
        recvd_cont_dict = xml_parse.extract_decrypted_msg(recvd_msg_dict['message'])
        response.status_code = status.HTTP_200_OK

        # 将消息塞入数据库，会有callback去消费消息
        db = DB()
        db.fetch()
        if db.existed(msgid= recvd_cont_dict['MsgId']):
            return 
        db.insert2(dict(
            content = recvd_cont_dict['Content'],
            nonce = nonce,
            timestamp = timestamp,
            recvd_cont_dict = json.dumps(recvd_cont_dict),
            receiveid = recvd_msg_dict['receiveid'],
            msgid = recvd_cont_dict['MsgId']
        ))
        db.existed(recvd_cont_dict['MsgId'])

        # rely_cont = reply_msg(recvd_cont_dict['Content'])
        # rply_cont_xml = xml_parse.generate(rely_cont, recvd_cont_dict)
        # return_code, r_encrypt_msg = WeComCrypt(
        #                                 CFG.C['WeCom']['Token'], 
        #                                 CFG.C['WeCom']['EncodingAESKey'],
        #                                 recvd_msg_dict['receiveid']
        #                             ).EncryptMsg(rply_cont_xml, nonce, timestamp)
        # log.debug(f"{return_code=}, {r_encrypt_msg=}")
        # if return_code != 0:
        #     return None
        # return r_encrypt_msg

        log.debug(f"Received from user: {recvd_cont_dict}")
    else:
        response.status_code = status.HTTP_403_FORBIDDEN
        log.warning("Invalid signature")
        return "Invalid signature"
    

@app.get('/wecom/accesstoken')
async def get_access_token(response: Response):
    url = CFG.C['WeCom']['URL']['ACCTK'] % (CFG.C['WeCom']['CorpID'], CFG.C['WeCom']['Secret'])
    res = await aget(url, verify_ssl=False)
    response.status_code = status.HTTP_200_OK
    return await res.json()




def run_server():
    log.debug("Running server")
    uvicorn.run(
        app,
        host=CFG.C['SERVER']['IP'],
        port=CFG.C['SERVER']['PORT']
    )


if __name__ == '__main__':
    run_server()