import logging
import pathlib
import json

from library.utils import CFG


class MyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name != ''
    

log_file = pathlib.Path("~/.AIGCSrv/fastapi-users-orm-demo.log").expanduser()
# log_file.touch(exist_ok=True)


LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s %(name)s %(filename)s %(funcName)s %(lineno)d %(levelprefix)s| %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
        },
        "console": {
            "format": "%(asctime)s %(name)s %(filename)s %(funcName)s %(lineno)d %(levelname)s| %(message)s",
        }
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "console": {
            "formatter": "console",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": "DEBUG"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "console",
            "filename": "/home/yohann/.AIGCSrv/chatgpt_srv.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "level": "DEBUG",
            "encoding": "utf8"
        }
    },
    "loggers": {
        "uvicorn": {"handlers": ["default", "file"], "level": "DEBUG", "propagate": False},
        "uvicorn.error": { "level": "INFO"},
        "uvicorn.access": {"handlers": ["access", "file"], "level": "INFO", "propagate": False},
        "app": {"handlers": ["console", "file"], "level": "DEBUG", 'propagate': False}
    },
    # 'root': {
    #     'handlers': ['console'],
    #     'level': 'DEBUG',
    #     'propagate': False
    # }
}

def get_log_config():
    with open(pathlib.Path(CFG.C['LOGCONFIG']['FP']).expanduser().as_posix()) as f:
        config = json.load(f)
        return config

# set_log_config()