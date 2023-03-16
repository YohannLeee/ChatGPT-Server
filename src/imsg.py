# -*- coding: UTF-8 -*-
import sqlite3
import pathlib
import typing
import logging
import sys
sys.path.append(
    pathlib.Path(__file__).parent.parent.as_posix()
)

from settings import conf
from utils import applescript

log = logging.getLogger('app.imsg')

class Imsg:
    def __init__(self) -> None:
        self.db = sqlite3.connect(pathlib.Path(conf.IMSG_DB_FP).expanduser().as_posix())
        self.cur = self.db.cursor()
        self.cur_time = 0
        self.set_cur_time()

    def get_latest_msgs(self) -> typing.List:
        """
        获取未读msgs
        """
        self.cur.execute(conf.GET_LATEST_MSGS.format(date=self.cur_time))
        # self.cur.execute(conf.GET_LATEST_MSGS.format(date='700560160686447872'))
        msgs = self.cur.fetchall()
        if len(msgs):
            log.debug(f"Fetched {len(msgs)} msgs, {msgs=}")
            self.set_cur_time((msgs[-1][2], ))
        return msgs

    def set_cur_time(self, msg = []) -> None:
        """
        初始化cur_time
        """
        if not msg:
            log.debug("Initializing current time")
            self.cur.execute(conf.GET_LATEST_DATE)
            msg = self.cur.fetchone()
        if len(msg) == 0:
            log.warning("Cannot get latest time in chat.db")
            log.debug(f"Got latest time result: {msg}")
        else:
            self.cur_time = msg[0]
            log.info(f"set cur_time to {self.cur_time}")
            
            
class Message:
    def __init__(self, msg: typing.Tuple):
        self.msg: typing.Text 
        self.msg, self.datetime, self.raw_date, self.sender_address, self.group_name, self.chat_id = msg

    def is_group(self) -> bool:
        if self.group_name:
            return True
        
    def __str__(self) -> str:
        return f"{self.group_name}|{self.chat_id}|{self.sender_address}|{self.msg}"


def send_imsg(chat_identifier: typing.Text, msg: typing.Text, **kwargs):
    log.debug(f"Send msg to {chat_identifier} {kwargs.get('group_name')} {kwargs.get('sender_address')}")
    content = conf.SEND_IMSG.format(chat_id=chat_identifier, msg=msg.replace('"', '\\"'))
    r = applescript.run(content)
    log.debug(f"Send msg exit code - {r.code}")
    if r.out:
        log.debug(f"Out: {r.out}")
    if r.err:
        log.error(f"Error: {r.err}")
        log.debug(f"Answer should be sent {content=}")
    


# imsg = Imsg()
# t = imsg.set_cur_time()
# print(t)

if __name__ == '__main__':
    # imsg = Imsg()
    # imsg.get_latest_msgs()
    chat_id = 'chat11796791165247130'
    msg = 'c.execute("SELECT date, text FROM message"'
    send_imsg(chat_identifier=chat_id, msg=msg)
    
    