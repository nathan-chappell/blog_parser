# util.py

import logging
import sys
from typing import List
from pathlib import Path
import re
from datetime import datetime, timedelta

def td2sec(td: timedelta) -> float:
    return td.seconds + td.microseconds/10**6

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

def smooth_split_i(s: str, w: int) -> int:
    if len(s) < w: return w
    i = w
    for i in range(w-1,w//2,-1):
        if s[i].isspace() or s[i] == '-': return i
    return w

def smooth_split(s:str, w: int) -> List[str]:
    paragraph: List[str] = []
    i = 0
    while i < len(s):
        j = smooth_split_i(s[i:i+w-4],w-4)
        paragraph.append(s[i:i+j].strip())
        i += j
    return paragraph

#
# print text with a * border
#
def bannerfy(s: str,banner_char='*') -> str:
    w = 80
    lpad = 1
    rpad = 1
    header = footer = banner_char*w
    l = banner_char + ' '*lpad
    r = ' '*rpad + banner_char
    row_fmt = l + "{s:" + str(w-lpad-rpad-2) + "}" + r
    onerow_fmt = l + "{s:^" + str(w-lpad-rpad-2) + "}" + r

    if len(s) == 0:
        return "\n" + header
    if len(s) < w-4 and "\n" not in s:
        return f"\n{header}\n" + onerow_fmt.format(s=s) + f"\n{footer}"
    else:
        res = "\n" + header + "\n"
        for p in s.split("\n"):
            for s in smooth_split(p,w-4):
                res += row_fmt.format(s=s) + "\n"
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

def get_new_name(old_name: str) -> str:
    name = ""
    while name in ["",old_name] or not name.isalnum():
        print('please enter a new alpha-numeric index name:')
        print(f'old name: {old_name}')
        name = input(input_prompt)
    return name

def assert_unique_first_letter(strs: List[str]):
    first_letters = set(map(lambda s: s[0],strs))
    assert len(first_letters) == len(strs), bannerfy(f"""
first letter of each string is not unique.  Probably an error in
input_command() (Change the list of input commands to ensure each has a unique
first letter).
""".replace("\n",' '))

def input_command(safe: List[str], dangerous: List[str] = []) -> str:
    commands = safe + dangerous
    assert_unique_first_letter(commands), 
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
