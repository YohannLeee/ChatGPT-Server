import asyncio
import logging
from typing import Generic, Sequence
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from email.message import Message

from library.fastapi_users_verification.models import MessageTransport
from library.fastapi_users_verification.schemas import M, MA, MailAccountModel, MailModel
from library.utils import CFG

account = MailAccountModel(
    mail_host=CFG.C['Mail']['host'],
    mail_port=CFG.C['Mail']['port'],
    mail_user=CFG.C['Mail']['user'],
    mail_password=CFG.C['Mail']['pswd']
)

class MailTransport(MessageTransport, Generic[M, MA]):
    """Mail protocol that build a mail sender should follow"""

    def __init__(self, account: MA) -> None:
        self.account = account

    async def send(self, message: M):
        _m = self._get_message(message)
        async with (await self._get_smtp_client(self.account)) as smtp_client:
            await smtp_client.send_message(_m)

    def _get_message(self, message: M) -> Message:
        _m = MIMEMultipart()
        # _m['From'] = message.sender
        _m['From'] = formataddr((CFG.C['Mail']['name'], message.sender))
        _m['To'] = ', '.join(message.to_address)
        _m['Subject'] = message.subject
        
        body = MIMEText(message.body, 'html')
        _m.attach(body)

        return _m

    async def _get_smtp_client(self, account: MA) -> aiosmtplib.SMTP:
        smtp_client = aiosmtplib.SMTP(hostname= account.mail_host, port= account.mail_port)
        await smtp_client.connect(use_tls=True)
        await smtp_client.login(account.mail_user, account.mail_password)
        return smtp_client

        
async def main():
    trans = MailTransport(account)
    await trans.send(MailModel(
            sender = CFG.C['Mail']['user'],
            to_address= ['lyh001686@sina.com'],
            subject='智远AI用户认证',
            body=f"亲爱的用户您好\n        感谢您注册使用智远AI，您的邮箱验证token是token"
            ))
    # await asyncio.sleep(3)
    return 0


if __name__ == '__main__':
    asyncio.run(main())