# util.py

import logging
import sys
from typing import List

log_dir = 'logs'

def get_log(source_filename: str, stderr=False):
    log_file = log_dir + '/' + source_filename.replace('.py','.log')
    fmt = '%(name)s:%(levelname)s:%(funcName)s: %(message)s'
    log = logging.getLogger(source_filename)
    log.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt)
    handlers: List[logging.Handler] = [logging.FileHandler(log_file)]
    if stderr: handlers.append(logging.StreamHandler(sys.stderr))
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
