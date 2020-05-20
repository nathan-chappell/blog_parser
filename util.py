# util.py

import logging
import sys
from typing import List
from pathlib import Path
import re


def word_count(s: str) -> int:
    return len(s.split())


log_dir = Path('./logs')
if not log_dir.exists():
    log_dir.mkdir()


def get_log(source_filename: str, stderr=False, mode='a'):
    name = Path(source_filename).name
    log_file = (log_dir / name).with_suffix('.log')
    if not log_file.exists():
        log_file.touch()
    fmt = '%(name)s:%(levelname)s:%(funcName)s: %(message)s'
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt)
    handlers: List[logging.Handler] = []
    handlers.append(logging.FileHandler(log_file, mode=mode))
    if stderr:
        handlers.append(logging.StreamHandler(sys.stderr))
    for handler in handlers:
        handler.setFormatter(formatter)
        log.addHandler(handler)
    return log

#
# print text with a * border
#
def bannerfy(s: str) -> str:
    w = 80
    lpad = 1
    rpad = 1
    header = footer = '*'*w
    l = '*' + ' '*lpad
    r = ' '*rpad + '*'
    row_fmt = l + "{s:" + str(w-lpad-rpad-2) + "}" + r
    onerow_fmt = l + "{s:^" + str(w-lpad-rpad-2) + "}" + r

    if len(s) == 0:
        return "\n" + header
    if len(s) < w-4 and "\n" not in s:
        return f"\n{header}\n" + onerow_fmt.format(s=s) + f"\n{footer}"
    else:
        res = "\n" + header + "\n"
        for p in s.split("\n"):
            i = 0
            while i < len(p):
                res += row_fmt.format(s=p[i:i+w-4]) + "\n"
                i += w-4
        return res + footer

#
# getting text from a user in a sane manner
#

input_prompt = "$ "

def confirm_command(msg: str = "") -> bool:
    msg_ = "?" if not msg else " you wish to " + msg + "?"
    message = "are you sure" + msg_
    print(message)
    while True:
        confirm = input("[y]es or [n]o: ").lower().strip()
        if confirm == "":
            continue
        elif re.match(confirm, 'yes'):
            return True
        elif re.match(confirm, 'no'):
            return False
        else:
            print('please enter y/ye/yes, or n/no')


def input_command(safe: List[str], dangerous: List[str] = []) -> str:
    commands = safe + dangerous
    prompt: List[str] = list(map(lambda s: f'[{s[0]}]{s[1:]}', commands))
    while True:
        print(f"enter command: {prompt}")
        cmd = input(input_prompt).lower().strip()
        if cmd == "":
            continue

        def matcher(s): return re.match(cmd, s) is not None
        candidates = list(filter(matcher, commands))
        if candidates:
            candidate = candidates[0]
            if candidate not in dangerous or confirm_command(candidate):
                return candidate
        else:
            print(f'Did not recognize: {cmd}')
