# experiments_analysis.py

from experiments_base import Result, Prediction, add_parent_dir_to_path
add_parent_dir_to_path()

from util import bannerfy # type: ignore

from typing import List, Callable, Union, Optional, Dict, Tuple
import yaml
import numpy as np # type: ignore
from pathlib import Path
import os
import sys

Key = Callable[[Result],Union[float,int]]

class DescriptiveStats(yaml.YAMLObject):
    _min: float
    _max: float
    _mean: float
    _std: float
    fmt: str

    def __init__(self, name, source, key: Optional[Key] = None, fmt='{:9.3f}'):
        self.fmt = fmt
        self.name = name
        data = []
        if key is not None:
            for item in source:
                data.append(key(item))
        else:
            data = source
        data = np.array(data)

        self._min = np.min(data)
        self._max = np.max(data)
        self._mean = np.mean(data)
        self._std = np.std(data)

    def __str__(self):
        name = f'{self.name:20}'
        formatter = '[' + ', '.join([self.fmt]*4) + ']'
        res = formatter.format(self._min,self._max,self._mean,self._std)
        return name + res + "  (min/max/mean/std)"
    
    def __repr__(self):
        return yaml.dump(self)


def analyze_results(results: List[Result]) -> List[DescriptiveStats]:
    def time_key(result: Result) -> float:
        return result.time
    def f1_key(result: Result) -> float:
        return result.predictions[0].f1
    def pr_key(result: Result) -> float:
        return result.predictions[0].pr
    def char_len_key(result: Result) -> float:
        return len(result.context)
    def word_len_key(result: Result) -> float:
        return len(result.context.split())

    #for result in results: 
        #print(result)
        #print("\n"+'_'*80)

    #keys = [time_key, f1_key, pr_key, char_len_key, word_len_key]
    keys = [f1_key, pr_key, time_key]
    names = [key.__name__[:key.__name__.find('_key')] for key in keys]
    return [DescriptiveStats(name,results,key) for name,key in zip(names,keys)]

stats_list: List[Tuple[str,DescriptiveStats]] = []

def analyze_all(directory: str):
    path = Path(directory)
    for p in path.glob('*.yml'):
        #print(p)
        with p.open() as yml:
            results: List[Result] = yaml.full_load(yml)
        stats = analyze_results(results)
        stats_list.append((str(p), stats))
        #for stat in stats:
            #print(stat)
        #print(stats[1])
        #print('#'*40)

def analyze_intial():
    results_filename = 'initial_results.yml'
    with open(results_filename) as file:
        y = yaml.load(file)
    stats = analyze_results(y)
    for stat in stats:
        print(stat)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('please enter the results directory',file=sys.stderr)
        exit(-1)
    directory = sys.argv[1]
    analyze_all(directory)
    stats_list = sorted(stats_list, key=lambda t: t[0])
    for t in stats_list:
        print(t[0])
        for stat in list(t[1]):
            print(stat)
        print('#'*40)

    print('#'*40)
    print('#'*40)
    stats_list = sorted(stats_list, key=lambda t: t[1][0]._mean, reverse=True)
    for t in stats_list:
        print(t[0])
        for stat in list(t[1]):
            print(stat)
        print('#'*40)

    f1s = np.array(list(map(lambda t: t[1][0]._mean, stats_list)))
    prs = np.array(list(map(lambda t: t[1][1]._mean, stats_list)))

    print('*'*4)
    print('*'*4, 'Correlation between pr and f1:', np.corrcoef(f1s,prs)[0,1])
    print('*'*4)
