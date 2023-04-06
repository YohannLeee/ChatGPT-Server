import pathlib
import sqlite3
import logging
import sys
sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())

from library.utils import CFG
from settings import conf

log = logging.getLogger('app.db')

class DB:
    __instance = None

    def __init__(self) -> None:
        self.conn, self.cur = self._init_db()

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def _init_db(self):
        db_fp_obj = pathlib.Path(CFG.C['DATA_DB_FP']).expanduser()
        if not db_fp_obj.exists():
            db_fp_obj.touch()
        log.debug(f"Initializing sqlite db {db_fp_obj.as_posix()}")
        conn = sqlite3.connect(db_fp_obj.as_posix())
        cur = conn.cursor()
        # 创建 data_list 表(content, nonce, timestamp, recvd_cont_dict, receiveid, msgid)
        cur.execute(conf.DATALIST_TABLE)
        cur.execute(conf.TRIGGER_TABLE)
        cur.execute(conf.TRIGGER)
        log.debug("DB initialized")
        return conn, cur
    
    def insert(self, data: dict):
        keys = []
        values = []
        for k,v in data.items():
            keys.append(k)
            values.append(v)
        columns = ', '.join(keys)
        row = ', '.join(['?' for _ in values])
        cmd = f"INSERT INTO data_list({columns}) VALUES({row});"
        r = self.execute(cmd, values)
        
        log.debug(f"{r=}")

    def insert2(self, data:dict):
        keys = []
        values = []
        for k,v in data.items():
            keys.append(k)
            values.append(v)
        columns = ', '.join(keys)
        row = ', '.join([repr(v) for v in values])
        cmd = f"INSERT INTO data_list({columns}) VALUES({row});"
        r = self.execute(cmd, )
        log.debug(f"{r=}")

    def delete(self, data: dict):
        _msgid = data['msgid']
        cmd = f"DELETE FROM data_list where msgid='{_msgid}';"
        r = self.execute(cmd)
        log.debug(f"{r=}")

    def fetch(self):
        cmd = "select content, nonce, timestamp, recvd_cont_dict, receiveid, msgid from data_list;"
        r = self.execute(cmd)
        # log.debug(f"{r=}")
        return r
    
    def existed(self, msgid:str) -> bool:
        cmd = f"select content from data_list where msgid='{msgid}';"
        r = self.execute(cmd)
        log.debug(r)
        return bool(r)

    def execute(self, cmd, args: list = []):
        # log.debug(f"{cmd=}, {args=}")
        if args:
            self.cur.execute(cmd, args)
        else:
            self.cur.execute(cmd)
        self.conn.commit()
        return self.cur.fetchall()


def main():
    CFG()
    log.debug(CFG.C)
    db = DB()
    db.insert2({'content': 'contenta', 'msgid': '12453'})
    pass


if __name__ == '__main__':
    main()
