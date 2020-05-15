# paragraph_stats.py

import numpy as np # type: ignore

Samples = List[float]
Stats = Dict[str,List[float]]

def handle_paragraph_stats(stats: Stats, paragraph: Paragraph):
    stats['paragraph_lengths'].append(float(len(paragraph.text.split())))
    print(paragraph)

class StatsFmt:
    fields = ['min','max','mean','std','sum']
    width = 6
    precision = 2
    label_width = 20

def minMaxMeanStdSum(samples: Samples):
    ffmt = f'0{StatsFmt.width}.{StatsFmt.precision}f'
    fmt = "["
    fmt += ", ".join(map(lambda s: f'{{{s}:{ffmt}}}', StatsFmt.fields))
    fmt += "]"
    X = np.array(samples)
    m, M = np.min(X), np.max(X)
    mu, std = np.mean(X), np.std(X)
    sum = np.sum(samples)
    return fmt.format(min=m,max=M,mean=mu,std=std,sum=sum)

def td2ms(td: timedelta):
    return (td.seconds + td.microseconds/10**6)*10**3

def format_stats(stats: Stats) -> str:
    header = ' '*StatsFmt.label_width
    header_fmt = f'  {{:{StatsFmt.width}}}'*len(StatsFmt.fields)
    header += header_fmt.format(*StatsFmt.fields)
    res = [header]
    fmt = f"{{label:{StatsFmt.label_width}}}{{pstats}}"
    for k,v in stats.items():
        pstats = minMaxMeanStdSum(stats[k])
        res.append(fmt.format(label=k,pstats=pstats))
    return "\n".join(res)

#def handle_files(
