# -*- encoding: utf-8 -*-
'''
@File    :   to_text.py
@Time    :   2023/03/17 10:03:39
@Author  :   Yohann Li
@Version :   1.0
@Contact :   intelligenct@gmail.com
@Desc    :   Receive voice binary and send request to baidu api for text
'''

# here put the import lib
import json
import threading
import logging
import time
import uuid
import wave
from typing import ByteString, Text, Generator
# import sys
# import pathlib
# sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())

import websocket

from settings.conf import APP_ID, APP_KEY, DEV_PID, HOST_MAC, URI

logger = logging.getLogger()

def send_start_params(ws):
    """
    开始参数帧
    :param websocket.WebSocket ws:
    :return:
    """
    req = {
        "type": "START",
        "data": {
            "appid": APP_ID,  # 网页上的appid
            "appkey": APP_KEY,  # 网页上的appid对应的appkey
            "dev_pid": DEV_PID,  # 识别模型
            "cuid": HOST_MAC,  # 随便填不影响使用。机器的mac或者其它唯一id，百度计算UV用。
            "sample": 16000,  # 固定参数
            "format": "pcm"  # 固定参数
        }
    }
    body = json.dumps(req)
    ws.send(body, websocket.ABNF.OPCODE_TEXT)
    logger.info("send START frame with params:" + body)

def send_binary_stream(ws: websocket.WebSocket, _gen: Generator):
    """
    接收数据流并发送
    """
    for _binary in _gen:
        ws.send(_binary, websocket.ABNF.OPCODE_BINARY)


def wav_file_stream(fp: Text, chunk_size: int = 1024) -> Generator:
    with wave.open(fp, "rb") as wf:
        while data := wf.readframes(chunk_size):
            yield data


class BaiDuVoiceAI:
    """
    百度智能云 - 语音转文字
    """
    def __init__(self):
        self.msg = dict()

    def on_message(self, ws: websocket.WebSocket, msg: Text):
        """
        接收服务端返回的消息
        :param ws:
        :param message: json格式，自行解析
        :return:
        """
        logger.debug(f"Response: {msg}")
        self.msg = msg

    def on_open(self, ws: websocket.WebSocket):
        """
        连接后发送数据帧
        :param  websocket.WebSocket ws:
        :return:
        """

        def run(*args):
            """
            发送数据帧
            :param args:
            :return:
            """
            send_start_params(ws)
            send_binary_stream(ws, self.audio_stream)
            send_finish(ws)
            logger.debug("thread terminating")

        threading.Thread(target=run).start()

    def voice2text(self, audio_stream: Generator) -> Text:
        self.audio_stream = audio_stream
        uri = f"{URI}?sn={str(uuid.uuid1())}"
        ws = websocket.WebSocketApp(uri,
            on_open=self.on_open,  # 连接建立后的回调
            on_message=self.on_message,  # 接收消息的回调
            on_error=on_error,  # 库遇见错误的回调
            on_close=on_close  # 关闭后的回调
        )
        ws.run_forever()
        logger.debug(f"语音转换文字完成: {self.msg}")
        return json.loads(self.msg)['result']



def send_audio(ws, pcm_file):
    """
    发送二进制音频数据，注意每个帧之间需要有间隔时间
    :param  websocket.WebSocket ws:
    :return:
    """
    chunk_ms = 160  # 160ms的录音
    chunk_len = int(16000 * 2 / 1000 * chunk_ms)
    with open(pcm_file, 'rb') as f:
        pcm = f.read()

    index = 0
    total = len(pcm)
    logger.info("send_audio total={}".format(total))
    while index < total:
        end = index + chunk_len
        if end >= total:
            # 最后一个音频数据帧
            end = total
        body = pcm[index:end]
        logger.debug("try to send audio length {}, from bytes [{},{})".format(len(body), index, end))
        ws.send(body, websocket.ABNF.OPCODE_BINARY)
        index = end
        time.sleep(chunk_ms / 1000.0)  # ws.send 也有点耗时，这里没有计算


def send_finish(ws):
    """
    发送结束帧
    :param websocket.WebSocket ws:
    :return:
    """
    req = {
        "type": "FINISH"
    }
    body = json.dumps(req)
    ws.send(body, websocket.ABNF.OPCODE_TEXT)
    logger.info("send FINISH frame")


def send_cancel(ws):
    """
    发送取消帧
    :param websocket.WebSocket ws:
    :return:
    """
    req = {
        "type": "CANCEL"
    }
    body = json.dumps(req)
    ws.send(body, websocket.ABNF.OPCODE_TEXT)
    logger.info("send Cancel frame")


def on_error(ws, error):
    """
    库的报错，比如连接超时
    :param ws:
    :param error: json格式，自行解析
    :return:
        """
    logger.error("error: " + str(error))


def on_close(ws, status, msg):
    """
    Websocket关闭
    :param websocket.WebSocket ws:
    :return:
    """
    logger.info(f"ws close w/ {status=}, {msg=}")
    ws.close()


def main():
    wav_fp = "D:\\projects\\ChatGPT-iMessage\\audio\\first_audio.wav"
    audio_stream = wav_file_stream(wav_fp, chunk_size=1024)
    bdai = BaiDuVoiceAI()
    msg = bdai.voice2text(audio_stream)
    logger.info(f"You said: {msg}")
    return 0


if __name__ == '__main__':
    main()