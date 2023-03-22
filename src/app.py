# -*- coding: utf-8 -*-

import argparse
import asyncio
import time
import logging
import sys
# import pathlib
# print(sys.path)

from settings import conf
from library.arguments import get_args
from AIGC import get_chat_bot, Chatbot
from iMessage.imsg import Imsg, Message, send_imsg
from iMessage.utils import in_whitelist, build_anwser, run_command
from server.AIGCServer import run_server

log = logging.getLogger('app')


def sync_imsg(chat: Chatbot, args: argparse.Namespace):
    imsg = Imsg()
    while True:
        msgs = imsg.get_latest_msgs()
        for msg in msgs:
            msg_obj = Message(msg)
            # 过滤安全名单
            if not in_whitelist(msg_obj):
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
                except Exception as e:
                    anwser = str(e)
                # log.debug(f"{content=}")
            elif msg_obj.msg[:3] == conf.CMD_FILTER:
                anwser = run_command(msg_obj.msg[3:], chat, msg_obj)
            else:
                continue
            # content = f"{question}\n---------------------------------\nA: {anwser}"
            if not anwser:
                continue
            content = build_anwser(msg_obj, anwser)
            send_imsg(msg_obj.guid, content, sender_address = msg_obj.sender_address, group_name = msg_obj.group_name)
        time.sleep(3)


def main():
    log.info(f"Running chatGPT + iMessage, version: {conf.VERSION}")
    args = get_args(sys.argv[1:])
    Chatbot = get_chat_bot(name= args.bot)
    chat = Chatbot(
        api_key= args.api_key,
        proxy= args.proxy,
        stream = args.stream,
        temperature=args.temperature
    )
    # chat.load_test()
    if args.imsg:
        sync_imsg(chat= chat, args = args)
    else:
        log.info("Running FastAPI server")
        run_server()
            


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit()
