# -*- coding: utf-8 -*-

import time
import logging
import sys
# import pathlib
# print(sys.path)

from settings import conf
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
            # 过滤msg格式
            if not msg_obj.msg.startswith(conf.MSG_FILTER):
                continue
            # 过滤安全名单
            if msg_obj.is_group():
                if not (msg_obj.chat_id in conf.ALLOW_GROUP_ID or msg_obj.group_name in conf.ALLOW_GROUP):
                    log.warning(f"Group not in white list")
                    log.debug(msg_obj.__str__())
                    continue
            else:
                if not msg_obj.sender_address in conf.ALLOW_USER:
                    log.warning(f"User not in white list")
                    log.debug(msg_obj.__str__())
                    continue
                
            question = msg_obj.msg
            sender = msg_obj.sender_address
            anwser = chat.ask(
                prompt= question[3:], 
                convo_id=sender if args.multi_turn else "default"
            )
            content = f"{question}\n---------------------------------\nA: {anwser}"
            send_imsg(msg_obj.chat_id, content, sender_address = msg_obj.sender_address, group_name = msg_obj.group_name)
        time.sleep(3)
            


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit()
