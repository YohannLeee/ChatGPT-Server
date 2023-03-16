import pathlib
import subprocess
import sys
sys.path.append(
    pathlib.Path(__file__).parent.parent.as_posix()
)

TEMPFP = '/tmp/imsg.scpt'


class Result:
    code = None
    out = None
    err = None

    def __init__(self,code,out,err):
        self.code = code
        self.out = out.decode("utf-8").rstrip()
        self.err = err.decode("utf-8").rstrip()


def run(script: str):
    # if Path(script).expanduser().exists():
    #     f = script
    # else:
    #     Path(TEMPFP).write_text(script)
    #     f = TEMPFP
    
    args = ["osascript", "-"]
    kwargs = dict(stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    proc = subprocess.Popen(args, **kwargs)
    out, err = proc.communicate(input = script.encode('utf8'))
    return Result(proc.returncode, out, err)


if __name__ == '__main__':
    cmd = f"""tell application "Messages"
set Group to chat id "iMessage;+;chat833779585482191616"
send "Test12" to Group
end tell"""
    cmd2 = """tell application "Messages"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy "chat11796791165247130" of targetService
    send "test" to targetBuddy
end tell
"""
    r = run(cmd2)
    print(r.code, r.out, r.err)
    