# experiments_analysis.py

from experiments import Result, Prediction
from util import bannerfy

from typing import List, Callable, Union, Optional
import yaml
import numpy as np # type: ignore

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

    for result in results: 
        print(result)
        print("\n"+'_'*80)

    keys = [time_key, f1_key, pr_key, char_len_key, word_len_key]
    names = [key.__name__[:key.__name__.find('_key')] for key in keys]
    return [DescriptiveStats(name,results,key) for name,key in zip(names,keys)]

if __name__ == '__main__':
    results_filename = 'initial_results.yml'
    with open(results_filename) as file:
        y = yaml.load(file)
    stats = analyze_results(y)
    for stat in stats:
        print(stat)
    print(np.corrcoef(np.stack
