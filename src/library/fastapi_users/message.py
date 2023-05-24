from enum import Enum


class Message(tuple[int, str], Enum):
    LOGIN_SUCCESS = (1, "登录成功")
    LOGOUT_SUCCESS = (1, "已退出登录")
    VERIFY_MAIL_SENT = (1, "验证邮件已发送")
    VERIFY_MAIL_OK = (1, "邮箱验证通过")
    RESET_PASSWORD_OK = (1, "密码已重置")

    USER_NOT_LOGIN = (102, "用户未登录")
    USER_INACTIVE = (103, "帐号已禁用")
    USER_NOT_VERIFIED = (104, "邮箱未验证")
    USER_NOT_SUPERUSER = (105, "用户权限不够")



def mk_json_res(msg: tuple[int, str], extension: dict = None) -> dict[str, int|str]:
    res = {}
    if isinstance(msg, tuple) and len(msg) == 2:
        res = {
            "code": msg[0],
            "message": msg[1]
        }
    if isinstance(msg, dict):
        res = msg
    if extension:
        res.update(extension)
    return res 
