import logging
import re
import pathlib

# Version
VERSION = "1.2"

logging.basicConfig(
    # filename="/tmp/chat_imsg.log",
    # filemode='a',
    datefmt='%F %T',
    format= "%(asctime)s %(name)s %(funcName)s %(lineno)s %(levelname)s | %(message)s",
    level = logging.DEBUG
)

prog_name = 'AIGCSrv'
conf_dir: pathlib.Path = pathlib.Path('~').expanduser() / f'.{prog_name}'
conf_fp: pathlib.Path = conf_dir / 'AIGC.yaml'
default_conf_fp: pathlib.Path = pathlib.Path(__file__).parent / 'AIGC.yaml'

# imsg db
IMSG_DB_FP = '~/Library/Messages/chat.db'

# Sqlite statement
GET_LATEST_MSGS = """
SELECT 
    m.text, 
    datetime(m.date / 1000000000 + strftime('%s', '2001-01-01'), 'unixepoch', 'localtime') as date, 
    m.date as raw_date,
    (CASE m.is_from_me WHEN 1 THEN SUBSTR(m.account,3) ELSE h.id END) as sender_address,
    c.display_name as group_name,
    -- (CASE c.display_name WHEN (length(c.display_name) != 0) THEN c.display_name ELSE '' END) as group_name,
    c.chat_identifier,
    c.guid
FROM
    message m 
    left join handle h on m.handle_id = h.rowid
    left join chat_message_join cm ON m.rowid = cm.message_id
    -- left join chat_handle_join ch ON m.handle_id = ch.handle_id
    left join chat c on cm.chat_id = c.rowid
WHERE
    m.date > {date}
    and m.associated_message_type = 0
    and m.text is not null
    and m.text != ' '
    and m.is_from_me = 0
ORDER BY 
m.date ASC;
"""
MSG_KEYS = ("msg", "datetime", "raw_date", "sender_address", "group_name", "chat_id", "guid")

GET_LATEST_DATE = "SELECT date FROM message ORDER BY rowid DESC LIMIT 1;"

# start with
MSG_FILTER = "Q: "
CMD_FILTER = "C: "
RESET_PATTERN = re.compile("reset ?(.*)?", flags=re.I)

# AppleScript cmd
SEND_IMSG1 = """tell application "Messages"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy "{guid}" of targetService
    send "{msg}" to targetBuddy
end tell
"""

SEND_IMSG2 = """tell application "Messages"
    set chatID to chat id "{guid}"
    send "{msg}" to chatID
end tell
"""
SEND_IMSG = SEND_IMSG2

# Baidu Voice API Const
APP_ID = 31348808
APP_KEY = "yMA2OLjVXUotLGUDrdjhTjGv"
DEV_PID = 15372
URI = "ws://vop.baidu.com/realtime_asr"
HOST_MAC = "0A-00-27-00-00-10"

# Help msg
HELP_MSG = """ChatGPT iMessage bot
使用方法: 
    提问方式 'Q: '+'你的问题'(Q+冒号+英文空格+问题)
    例如 'Q: 请帮我写一段C函数，要求传入一个数组完成自动排序，可以通过参数控制升序或降序'

    命令 'C: '+'命令'(C+冒号+英文空格+命令)
        help, 显示帮助信息
        test, 测试程序是否存活
        token, 获取已使用的token数量
        enable_history, eh, 允许bot读取历史记录
        disable_history, dh, 禁止bot读取历史记录
        reset, 开启enable_history后使用该命令可以清空机器人记录的聊天记录
    例如 'C: reset'

注意: 
1）语句开头Q: 要用!!!英文空格!!!
2）机器人当前采用的是识别用户聊天+单轮聊天模式，即bot读取每个用户的下一个问题时不会有上一个问题的记忆，要开启多轮聊天需输入命令'C: enable_history'"""

# 创建数据库表
DATALIST_TABLE = """CREATE TABLE IF NOT EXISTS data_list (
    content TEXT,
    nonce TEXT,
    timestamp TEXT,
    recvd_cont_dict TEXT,
    receiveid TEXT,
    msgid TEXT
);
"""
TRIGGER_TABLE = """CREATE TABLE IF NOT EXISTS consumed_data (
    content TEXT,
    nonce TEXT,
    timestamp TEXT,
    recvd_cont_dict TEXT,
    receiveid TEXT,
    msgid TEXT,
    event_time TEXT
);
"""

TRIGGER = """CREATE TRIGGER IF NOT EXISTS "record_consumed_data" AFTER DELETE
ON data_list
BEGIN
    insert into consumed_data(content, nonce, timestamp, recvd_cont_dict, receiveid, msgid, event_time) VALUES (OLD.content, OLD.nonce, OLD.timestamp, OLD.recvd_cont_dict, OLD.receiveid, OLD.msgid, datetime('now', 'localtime'));
END;
"""
