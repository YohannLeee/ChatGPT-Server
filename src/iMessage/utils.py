from typing import Text
import logging


from iMessage.imsg import Message
from AIGC.ChatGPT import Chatbot
from settings import conf
from library.utils import add_user, rm_user, CFG

log = logging.getLogger('imsg.utils')



def in_whitelist(msg: Message, CFG: dict) -> bool:
    """
    Check if sender or group in msg is allowed

    Args:
        msg_obj (Message): Message Object

    Returns:
        bool: True allowed, False not allowed
    """
    if msg.is_group():
        if not (msg.chat_id in CFG['imsg']['allow']['group_id'] or msg.group_name in CFG['imsg']['allow']['group']):
            log.warning(f"Group not in white list")
            log.debug(msg.__str__())
            return False
        log.debug(f"Group {msg.group_name or msg.group_name} is in white list")
    else:
        if not msg.sender_address.lower() in CFG['imsg']['allow']['user']:
            log.warning(f"User not in white list")
            log.debug(msg.__str__())
            return False
        log.debug(f"User {msg.sender_address} is in white list")
    return True


def build_anwser(msg: Message, anwser: Text) -> Text:
    """
    Generate formated anwser
    if from user, return content
    else return 
    '@sender
    conent'

    Args:
        msg (Message): Message object
        anwser (Text): text

    Returns:
        Text: formated anwser
    """
    if msg.is_group():
        sender_name = get_sender_name(msg.sender_address)
        result = f"@{sender_name}\n{anwser}"
    else:
        result = anwser
    return result

def get_sender_name(imsg_addr: Text) -> Text:
    """
    Get sender address
        abc@*.* -> abc
        abc.*@*.* -> abc
        imsg-abc@*.* -> abc
        imsg-abc.*@*.* -> abc
        +86* -> +86*


    Args:
        imsg_addr (Text): imsg sender address

    Returns:
        Text: sender name
    """
    if '@' in imsg_addr:
        sender_name = imsg_addr.split('@')[0]
        sender_name = sender_name.replace('imsg-', '')
        sender_name = sender_name.split('.')[0]
    else:
        sender_name = imsg_addr
    return sender_name


def run_command(cmd: Text, chat: Chatbot, msg: Message) -> Text:
    """Run command if received 'C: *'

    Args:
        cmd (Text): command

    Returns:
        Text: feedback
    """
    cmd = cmd.strip().lower()
    if not cmd:
        log.debug(f"Empty command")
        return ""
    match cmd.split():
        case ['help']:
            return conf.HELP_MSG
        case ['test']:
            return "Yeah, I'm still here"
        case ['enable_history'] | ['eh']:
            # 如果没有该用户的session，新建一个
            if msg.sender_address not in chat.conversation:
                chat.new_user(msg.sender_address)
            chat.conversation[msg.sender_address]['use_history'] = True
            return "Done"
        case ['disable_history'] | ['dh']:
            # 如果没有该用户的session，新建一个
            if msg.sender_address not in chat.conversation:
                chat.new_user(msg.sender_address)
            chat.conversation[msg.sender_address]['use_history'] = False
            return "Done"
        case ['reset', *prompt]:
            chat.reset(convo_id=msg.sender_address, system_prompt= ' '.join(prompt) if prompt else '')
            return "Chat reseted"
        case ['token', *name]:
            if name and name[0] == 'all':
                result = '\n'.join([f"{get_sender_name(convo_id)}: {chat.token_usage(convo_id)}" for convo_id in chat.conversation])
                result = f"以下是token使用统计信息\n{result}"
            else:
                result = f"您已使用token {chat.token_usage(msg.sender_address)}"
            return result
        case ['add_user', *users]:
            if not users:
                return "请提供要添加的users"
            r = add_user(users)
            _users = '\n'.join(r)
            return f"Done, 当前users: {_users}"
        case ['rm_user', *users]:
            if not users:
                return "请提供要删除的users"
            error, r = rm_user(users)
            if error:
                return r
            _users = '\n'.join(r)
            return f"Done, 当前users: {_users}"
        case ['user', *_]:
            return '\n'.join(CFG.C['imsg']['allow']['user'])
        case _:
            return f"Wrong command\n{conf.HELP_MSG}"
    # return ""