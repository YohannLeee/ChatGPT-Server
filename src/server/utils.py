import socket
import logging
from typing import Iterable
from xml.etree import ElementTree as ET

from aiohttp import ClientSession, ClientResponse

log = logging.getLogger('app.srv.util')


async def request(method: str, url: str, **kwargs) -> ClientResponse:
    async with ClientSession() as ss:
        res = await ss.request(method, url, **kwargs)
        return res
    

async def aget(*args, **kwargs) -> ClientResponse:
    return await request('GET', *args, **kwargs)


async def apost(*args, **kwargs) -> ClientResponse:
    return await request('POST', *args, **kwargs)


def get_ip():
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
    return ip


class XMLParse:
    """
    对接收到的和要发送给企业微信的消息进行xml格式化
    """

    # 未加密的消息模版
    REPLY_TEXT_PENDING_ENCRYPT = """<xml>
<ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
<FromUserName><![CDATA[%(FromUserName)s]]></FromUserName>
<CreateTime>%(CreateTime)s</CreateTime>
<MsgType><![CDATA[%(MsgType)s]]></MsgType>
<Content><![CDATA[%(Content)s]]></Content>
<MsgId>%(MsgId)s</MsgId>
<AgentID>%(AgentID)s</AgentID></xml>"""

    @staticmethod
    def extract(xml_text: str|bytes, keys: list|dict|tuple) -> dict:
        """提取企业微信发送的信息内容

        Args:
            xml_text (str | bytes): 解密后的xml字符串
            keys (Iterable): xml包含的key list

        Returns:
            dict: {k,...}
        """
        if isinstance(xml_text, bytes):
            xml_text = xml_text.decode()
        log.debug(f"{xml_text=}")
        xml_tree = ET.fromstring(xml_text)
        if isinstance(keys, dict):
            msg_type = xml_tree.find('MsgType').text
            _keys = keys.get(msg_type)
        else:
            _keys = keys
        if not _keys:
            log.error(f"Empty keys for msg_type {msg_type}, {xml_text=}, {_keys=}")
            return {}
        try:
            result = {k: xml_tree.find(k).text for k in _keys} # type: ignore
        except AttributeError as e:
            log.error(e)
            log.info(f"{xml_text=}, {_keys=}")
        log.debug(f"{result=}")
        return result

    def extract_msg(self, xml_text: str|bytes) -> dict:
        """提取企业微信post请求发送的 body

        Args:
            xml_text (str): 企业微信post请求发送的 body

        Returns:
            dict: {ToUserName, AgentID, Encrypt}
        """
        keys = ('ToUserName', 'AgentID', 'Encrypt')
        return self.extract(xml_text, keys)
    
    def extract_decrypted_msg(self, xml_text: str|bytes) -> dict:
        """提取企业微信发送的信息内容

        Args:
            xml_text (str | bytes): 解密后的xml字符串

        Returns:
            dict: 
                text: {ToUserName, FromUserName, CreateTime, MsgType, Content, MsgId, AgentID}
                voice: {ToUserName, FromUserName, CreateTime, MsgType, MediaId, MsgId, AgentID}
        """
        keys = {
            'text': ('ToUserName', 'FromUserName', 'CreateTime', 'MsgType', 'Content', 'MsgId', 'AgentID'),
            'voice': ('ToUserName', 'FromUserName', 'CreateTime', 'MsgType', 'MediaId', 'Format', 'MsgId', 'AgentID'),
        }
        return self.extract(xml_text, keys)

    def generate(self, reply: str, content: dict) -> str:
        """生成未加密的content xml body

        Args:
            reply (str): 待回复的文字信息
            content (dict): 回复的消息xml body，用来替换其中的Content

        Returns:
            str: content xml text body
        """
        content['Content'] = reply
        content_xml_body = self.REPLY_TEXT_PENDING_ENCRYPT % content
        return content_xml_body


    
def main():
    get_ip()
    pass


if __name__ == '__main__':
    main()
