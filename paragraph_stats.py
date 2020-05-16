# paragraph_stats.py

from paragraph import Paragraph
from util import get_log

import numpy as np # type: ignore
from typing import Iterable, List, Dict
from datetime import datetime, timedelta

Samples = List[float]
Label = str
Stats = Dict[Label,Samples]

# logging

log = get_log(__file__,mode='w') # mode 'w' to overwrite

def log_info(paragraph: Paragraph, length: float, time: float):
    id_ = f'{paragraph.filename}|{paragraph.paragraph_title}'
    log.info(f'[length:{length:8.0f}, time:{time:8.2f}] {id_}')

# formatting

class StatsFmt:
    fields: List[str] = ['min','max','mean','std','sum']
    width: int = 7
    precision: int = 2
    label_width: int = 20
    stats: Stats

    def minMaxMeanStdSum(self, samples: Samples):
        ffmt = f'0{self.width}.{self.precision}f'
        fmt = "["
        fmt += ", ".join(map(lambda s: f'{{{s}:{ffmt}}}', self.fields))
        fmt += "]"
        X = np.array(samples)
        m, M = np.min(X), np.max(X)
        mu, std = np.mean(X), np.std(X)
        sum = np.sum(samples)
        return fmt.format(min=m,max=M,mean=mu,std=std,sum=sum)

    def format_stats(self, stats: Stats) -> str:
        header = ' '*self.label_width
        header_fmt = f'  {{:{self.width}}}'*len(self.fields)
        header += header_fmt.format(*self.fields)
        res = [header]
        fmt = f"{{label:{self.label_width}}}{{pstats}}"
        for k,v in stats.items():
            pstats = self.minMaxMeanStdSum(stats[k])
            res.append(fmt.format(label=k,pstats=pstats))
        return "\n".join(res)

# collecting (need reducing function)

def td2ms(td: timedelta):
    return (td.seconds + td.microseconds/10**6)*10**3

class ParagraphStatsCollector:
    stats: Stats
    split: datetime
    statsFmt: StatsFmt

    def __init__(self, statsFmt = StatsFmt()):
        self.stats = {
            'paragraph_lengths': [],
            'parse_times_ms': [],
        }
        self.statsFmt = statsFmt
        self.split = datetime.now()

    def __call__(self, paragraph: Paragraph) -> Paragraph:
        l = len(paragraph.text.split())
        t = td2ms(datetime.now() - self.split)
        self.stats['paragraph_lengths'].append(l)
        self.stats['parse_times_ms'].append(t)
        self.split = datetime.now()
        log_info(paragraph, l, t)
        return paragraph

    def formatted(self) -> str:
        return self.statsFmt.format_stats(self.stats)


def handle_paragraph_stats(stats: Stats, paragraph: Paragraph):
    stats['paragraph_lengths'].append(float(len(paragraph.text.split())))
    print(paragraph)

