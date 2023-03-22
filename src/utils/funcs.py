import logging
from typing import Set, Text
import re

from imsg import Message
from settings import conf
# from chat import Chatbot

log = logging.getLogger("app.funcs")

def get_filtered_keys_from_object(obj: object, *keys: str) -> Set[str]:
    """
    Get filtered list of object variable names.
    :param keys: List of keys to include. If the first key is "not", the remaining keys will be removed from the class keys.
    :return: List of class keys.
    """
    class_keys = obj.__dict__.keys()
    log.debug(f"{class_keys=}")
    if not keys:
        return class_keys

    # Remove the passed keys from the class keys.
    if keys[0] == "not":
        return {key for key in class_keys if key not in keys[1:]}
    # Check if all passed keys are valid
    if invalid_keys := set(keys) - class_keys:
        raise ValueError(
            f"Invalid keys: {invalid_keys}",
        )
    # Only return specified keys that are in class_keys
    return {key for key in keys if key in class_keys}


def in_whitelist(msg: Message) -> bool:
    """
    Check if sender or group in msg is allowed

    Args:
        msg_obj (Message): Message Object

    Returns:
        bool: True allowed, False not allowed
    """
    if msg.is_group():
        if not (msg.chat_id in conf.ALLOW_GROUP_ID or msg.group_name in conf.ALLOW_GROUP):
            log.warning(f"Group not in white list")
            log.debug(msg.__str__())
            return False
        log.debug(f"Group {msg.group_name or msg.group_name} is in white list")
    else:
        if not msg.sender_address.lower() in conf.ALLOW_USER:
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
        sender_name = sender_name.lstrip('imsg-')
        sender_name = sender_name.split('.')[0]
    else:
        sender_name = imsg_addr
    return sender_name


def run_command(cmd: Text, chat, msg: Message) -> Text:
    """Run command if received 'C: *'

    Args:
        cmd (Text): command

    Returns:
        Text: feedback
    """
    if not cmd:
        log.debug(f"Empty command")
        return 
    if conf.RESET_PATTERN.search(cmd):
        system_prompt = conf.RESET_PATTERN.search(cmd).group(1)
        chat.reset(convo_id=msg.sender_address, system_prompt=system_prompt or chat.system_prompt)
        return f"Chat reseted{' to '+system_prompt if system_prompt else ''}"
    if cmd == 'test':
        return "Yeah, I'm still here"

