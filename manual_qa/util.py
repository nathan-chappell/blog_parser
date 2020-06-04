# util.py

import os
import logging
from logging import DEBUG, WARN
from pathlib import Path
from typing import List

def is_test(): 
    return os.environ.get('TEST',False)

def get_logger(filename):
    path_ = Path(filename)
    path = 'logs/' + path_.name.replace('.py','.log')
    log = logging.getLogger(path)
    formatter = logging.Formatter('%(name)s %(funcName)s %(levelname)s %(message)s')
    handlers = [
            logging.FileHandler(path),
            logging.StreamHandler()
    ]
    for handler in handlers: 
        handler.setFormatter(formatter)
        log.addHandler(handler)
    if is_test():
        log.setLevel(DEBUG)
    else:
        log.setLevel(DEBUG)
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


