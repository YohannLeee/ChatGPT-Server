import logging
import pathlib
from typing import Set
import yaml

# from chat import Chatbot
# import pathlib
# sys.path.append(
#     pathlib.Path(__file__).parent.parent.as_posix()
# )
from settings import conf

log = logging.getLogger("app.funcs")

def get_filtered_keys_from_object(obj: object, *keys: str) -> Set[str]:
    """
    Get filtered list of object variable names.
    :param keys: List of keys to include. If the first key is "not", the remaining keys will be removed from the class keys.
    :return: List of class keys.
    """
    class_keys = obj.__dict__.keys()
    # log.debug(f"{class_keys=}")
    if not keys:
        return set(class_keys)

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


def parse_config_file(fp: pathlib.Path) -> dict:
    if not fp.exists():
        fp.parent.mkdir(parents= True, exist_ok= True)
        fp.write_bytes(conf.default_conf_fp.read_bytes())
    _conf = yaml.load(fp.read_text(encoding='utf-8'), yaml.FullLoader)
    log.debug(f"{_conf=}")
    if not _conf.get('enable'):
        log.error(f"配置文件未启用, 请将配置文件中的 enable 设为 true: {fp.as_posix()}")
        raise Exception(f'配置文件未启用, 请将配置文件中的 enable 设为 true: {fp.as_posix()}')
    return _conf

class CFG:
    C = {}
    def __new__(cls, fp = conf.conf_fp):
        if not cls.C:
            cls.C = parse_config_file(fp)
        return cls
    
    @classmethod
    def reload(cls, fp = conf.conf_fp):
        cls.C = parse_config_file(fp)
        log.debug("CFG reloaded")

CFG()

def write_yaml(conf: dict, fp: pathlib.Path = conf.conf_fp):
    with open(fp, 'w') as f:
        yaml.dump(conf, f)

def add_user(users: list[str]):
    CFG.C['imsg']['allow']['user'].update({k:1 for k in users})
    log.debug(f"Added users {users}")
    write_yaml(CFG.C)
    CFG.reload()
    return CFG.C['imsg']['allow']['user']

def rm_user(users: list[str]):
    status = 0
    for user in users:
        try:
            CFG.C['imsg']['allow']['user'].pop(user)
        except KeyError:
            status = 1
            return status, f"User not found, {user}"
    log.debug(f"Removed users {users}")
    write_yaml(CFG.C)
    CFG.reload()
    return status, CFG.C['imsg']['allow']['user']

def main():
    parse_config_file(conf.conf_fp)
    pass


if __name__ == '__main__':
    main()