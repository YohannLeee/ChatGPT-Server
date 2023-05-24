from library.fastapi_users_verification.schemas import MailAccountModel
from library.utils import CFG


MAIL_ACCOUNT = MailAccountModel(
    mail_host=CFG.C['Mail']['host'],
    mail_port=CFG.C['Mail']['port'],
    mail_user=CFG.C['Mail']['user'],
    mail_password=CFG.C['Mail']['pswd']
)


# 用户邮箱未认证的情况下
# 通过 POST /auth/request-verify-token
# 请求发送邮箱验证链接
REQUEST_VERIFY_BODY = """<p style="font-size:16px;">尊敬的用户：您好！</p>
<div style="padding-left:20px;">
    <p>您正在提交对<code style="
    background-color: var(--md-code-bg-color);
    -webkit-box-decoration-break: clone;
    font-size: 0.85em;
    word-break: break-word;
    border-radius: 0.1rem;
    padding: 0px 0.294118em;>%(mail)s</code>的验证，请点击以下链接完成邮箱验证（如果不是您提交的申请，请忽略）。</p>

    <p>验证链接： <a href="%(verify_url)s">点击此处进行验证</a></p>
    <br>
    <p>%(verify_url)s</p>

    <p>如果以上链接无法点击，可以复制以上链接在浏览器打开。</p>
    <br>

    <p>智远AI</p>
    <p>此为系统邮件请勿回复</p>
</div>"""


# 用户忘记密码的情况下
# 通过 POST /auth/forgot-password
# 请求发送邮箱验证链接
FORGOT_PASSWORD_BODY = """<p style="font-size:16px;">尊敬的用户：您好！</p>
<div style="padding-left:20px;">
    <p>您正在提交对用户<code style="
    background-color: var(--md-code-bg-color);
    -webkit-box-decoration-break: clone;
    font-size: 0.85em;
    word-break: break-word;
    border-radius: 0.1rem;
    padding: 0px 0.294118em;>%(mail)s</code>更改密码的需求，请点击以下链接完成密码重置（如果不是您提交的申请，请忽略）。</p>

    <p>验证链接： <a href="%(url)s">点击此处重置密码</a></p>
    <br>
    <p>%(url)s</p>

    <p>如果以上链接无法点击，可以复制以上链接在浏览器打开。</p>
    <br>

    <p>智远AI</p>
    <p>此为系统邮件请勿回复</p>
</div>"""