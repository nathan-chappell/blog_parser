# util.py

import logging

log_dir = 'logs'

def get_log(source_filename: str):
    log_file = log_dir + '/' + source_filename.replace('.py','.log')
    fmt = '%(name)s:%(levelname)s:%(funcName)s: %(message)s'
    log = logging.getLogger(source_filename)
    log.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log

def bannerfy(s: str) -> str:
    w = 80
    lpad = 1
    rpad = 1
    header = footer = '*'*w
    l = '*' + ' '*lpad
    r = ' '*rpad + '*'

    if len(s) < w-4:
        return f"{header}\n{l}{s:^80}{r}\n{footer}" 
    else:
        i = 0
        s = header + "\n"
        while i < len(s):
            s += l + s[i:i+w-4] + r + "\n"
            i += w-4
        return s + footer
