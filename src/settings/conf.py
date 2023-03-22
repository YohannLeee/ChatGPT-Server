import logging
import re

# Version
VERSION = "1.1"

logging.basicConfig(
    # filename="/tmp/chat_imsg.log",
    filemode='a',
    datefmt='%F %T',
    format= "%(asctime)s %(name)s %(funcName)s %(lineno)s %(levelname)s | %(message)s",
    level = logging.DEBUG
)
# chat model
model_turbo = 'gpt-3.5-turbo'
model_0301 = 'gpt-3.5-turbo-0301'

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


# Allow user and group name
# limit 99 
ALLOW_USER_ = ["yohannlee@icloud.com", "kevinnn.wang@luxshare-icgt.com", "bruce.huang@luxshare-ict.com", "+8613564869282", "grace.su@luxshare-ict.com"]
ALLOW_USER = dict(zip(
    ALLOW_USER_,
    range(1, 100)
))
ALLOW_GROUP_ = []
ALLOW_GROUP = dict(zip(
    ALLOW_GROUP_,
    range(1, 100)
))
ALLOW_GROUP_ID_ = ["chat820181500141257725", "chat28234882383587646"]
ALLOW_GROUP_ID = dict(zip(
    ALLOW_GROUP_ID_,
    range(1, 100)
))

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