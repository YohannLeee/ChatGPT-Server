# -*- coding: utf-8 -*-

import time
import logging
import sys
# import pathlib
# print(sys.path)

from settings import conf
from utils.funcs import in_whitelist, build_anwser, run_command
from utils.arguments import get_args
from chat import Chatbot
from imsg import Imsg, Message, send_imsg

log = logging.getLogger('app')


def main():
    log.info(f"Running chatGPT + iMessage, version: {conf.VERSION}")
    args = get_args(sys.argv[1:])
    imsg = Imsg()
    chat = Chatbot(
        api_key= args.api_key,
        proxy= args.proxy,
        stream = args.stream,
        use_history=args.use_history,
        temperature=args.temperature
    )
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
            content = build_anwser(msg_obj, anwser)
            send_imsg(msg_obj.guid, content, sender_address = msg_obj.sender_address, group_name = msg_obj.group_name)
        time.sleep(3)
            


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit()
