# -*- coding: utf-8 -*-

import argparse
import asyncio
import json
import time
import logging
import logging.config
import sys
# import pathlib
# print(sys.path)

from settings import conf
from library.arguments import get_args
from AIGC import get_chat_bot, Chatbot
from iMessage.imsg import Imsg, Message, send_imsg
from iMessage.utils import in_whitelist, build_anwser, run_command
from server.server import run_server
from library.utils import CFG
from library.db import DB
from library.baidu_api import wav_file_to_text
# from library.WeCom.WXBizMsgCrypt3 import WXBizMsgCrypt as WeComCrypt
from WeCom.Message import send_text_to_app, download_temp_media, amr2pcm, download_high_definition_voice_material
import exceptions
from settings.log import get_log_config

logging.config.dictConfig(get_log_config())
log = logging.getLogger('app')
cfg = CFG().C


def sync_imsg(chat: Chatbot, args: argparse.Namespace):
    imsg = Imsg(CFG= CFG)
    while True:
        msgs = imsg.get_latest_msgs()
        for msg in msgs:
            msg_obj = Message(msg)
            # 过滤安全名单
            if not in_whitelist(msg_obj, cfg):
                continue

            # 过滤msg格式
            anwser = ""
            if msg_obj.msg[:3] == conf.MSG_FILTER:
                question = msg_obj.msg
                sender = msg_obj.sender_address
                try:
                    anwser = chat.ask(
                        prompt= question[3:], 
                        convo_id=sender if args.multi_people else "default"
                    )
                except exceptions.ModelOverloaded as e:
                    anwser = e.reason
                except Exception as e:
                    anwser = str(e)
                    log.exception(e)
                # log.debug(f"{content=}")
            elif msg_obj.msg[:3] == conf.CMD_FILTER:
                anwser = run_command(msg_obj.msg[3:], chat, msg_obj)
            else:
                continue
            # content = f"{question}\n---------------------------------\nA: {anwser}"
            if not anwser:
                continue
            content = build_anwser(msg_obj, anwser)
            try:
                send_imsg(msg_obj.guid, content, sender_address = msg_obj.sender_address, group_name = msg_obj.group_name)
            except Exception as e:
                send_imsg(msg_obj.guid, str(e), sender_address = msg_obj.sender_address, group_name = msg_obj.group_name)
                log.exception(e)
                
        time.sleep(3)

def anwser(chat: Chatbot, args: argparse.Namespace):
    # xml_parse = XMLParse()
    db = DB()
    while True:
        time.sleep(3)
        data = db.fetch()
        if not data:
            continue

        for row_ in data:
            # _, nonce, timestamp, _, receiveid, msgid = row_
            recvd_cont_dict = json.loads(row_[3])
            log.info(f"Dealing with msg: {recvd_cont_dict=}, Content: {recvd_cont_dict.get('Content', recvd_cont_dict.get('MediaId'))}")
            if recvd_cont_dict['MsgType'] == 'text':
                content = recvd_cont_dict['Content']
            elif recvd_cont_dict['MsgType'] == 'voice':
                # continue
                media_id = recvd_cont_dict['MediaId']
                amr_fp = download_temp_media(media_id= media_id, fn=recvd_cont_dict['MsgId'])
                # amr_fp = download_high_definition_voice_material(media_id= media_id, fn=recvd_cont_dict['MsgId'])  # invalid media_id, https://open.work.weixin.qq.com/devtool/query?e=40007'
                if not amr_fp:
                    log.error(f"Error while geting media with media_id {media_id}")
                    db.delete({'msgid': recvd_cont_dict['MsgId']})
                    continue
                wav_fp = amr_fp.replace(".amr", ".wav")
                exit_code = amr2pcm(amr_fp, wav_fp)
                if exit_code != 0:
                    log.error(f"Error while convert .amr to .wav, exit code = {exit_code}")
                    db.delete({'msgid': recvd_cont_dict['MsgId']})
                    continue
                content = wav_file_to_text(wav_fp)
                if not content:
                    log.debug(f"Empty content")
                    db.delete({'msgid': recvd_cont_dict['MsgId']})
                    continue
                send_text_to_app(content= f"识别到您的问题：{content}", recvd_cont_dict= recvd_cont_dict)
                log.debug(f"Content converted from voice data: {content}")
            else:
                log.error(f"Not supported MsgType {bytes(recvd_cont_dict['MsgType']).decode('unicode_escape')}")
                continue
            user_name = recvd_cont_dict['FromUserName']
            rply_cont = chat.ask(content, convo_id=user_name)
            # rply_cont = '这是我的答案'
            log.info(f"Send to user {user_name}: {rply_cont}")
            send_text_to_app(content= rply_cont, recvd_cont_dict= recvd_cont_dict)
            db.delete({'msgid': recvd_cont_dict['MsgId']})
            log.info(f"Deleted msg {recvd_cont_dict['MsgId']}")
            # rply_cont_xml = xml_parse.generate(rely_cont, recvd_cont_dict)
            # return_code, r_encrypt_msg = WeComCrypt(
            #                                 CFG.C['WeCom']['Token'], 
            #                                 CFG.C['WeCom']['EncodingAESKey'],
            #                                 receiveid
            #                             ).EncryptMsg(rply_cont_xml, nonce, timestamp)
            # db.delete(dict(msgid= msgid))
            # log.debug(f"{return_code=}, {r_encrypt_msg=}")
            # if return_code != 0:
            #     log.warning(f"{return_code}")
            #     return None
            # return r_encrypt_msg



async def main():
    log.info(f"Running chatGPT Server, version: {conf.VERSION}")
    args = get_args(sys.argv[1:])
    Chatbot = get_chat_bot(name= args.bot)
    chat = Chatbot(
        api_key= args.api_key,
        proxy= args.proxy,
        stream = args.stream,
        temperature=args.temperature,
    )
    # chat.load_test()
    if args.execute == 'imsg':
        sync_imsg(chat= chat, args = args)
    elif args.execute == 'srv_callback':
        log.info(f"Running as server callback")
        anwser(chat, args)
    elif args.execute == 'server':
        log.info(f"Running FastAPI server as WEB server")
        await run_server(port = args.port)
            


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("\nKeyboardInterrupted, exiting...")
    except Exception as e:
        log.exception(e)
    finally:
        sys.exit()
