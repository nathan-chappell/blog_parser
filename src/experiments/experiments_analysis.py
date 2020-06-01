# experiments_analysis.py

from experiments_base import Result, Prediction, add_parent_dir_to_path
add_parent_dir_to_path()
from util import bannerfy # type: ignore

import elasticsearch # type: ignore

from typing import List, Callable, Union, Optional, Dict, Tuple, Any
import yaml
import numpy as np # type: ignore
from pathlib import Path
import os
import sys
import re

Key = Callable[[Result],Union[float,int]]

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

def context_key(result: Result) -> str:
    return result.context

es = elasticsearch.Elasticsearch()

def prediction_context_key(result: Result) -> str:
    prediction = result.predictions[0]
    try:
        doc_id = prediction.metadata['document_id']
        index = prediction.metadata['index']
        es_doc = es.get(index=index,id=doc_id)
        return es_doc['_source']['text']
    except elasticsearch.ElasticsearchException as e:
        # maybe handle later...
        raise e

def build_query(result: Result) -> Dict[str,Any]:
    return {'query':
            {'bool':
                {'should':[{'multi_match': {
                    'query':result.question,
                    'type':'most_fields',
                    'fields':['text','title'],
            }}]}}}

def relevance_key(result: Result) -> float:
    prediction = result.predictions[0]
    try:
        doc_id = prediction.metadata['document_id']
        index = prediction.metadata['index']
        es_exp = es.explain(index=index,id=doc_id,body=build_query(result))
        return es_exp['explanation']['value']
    except elasticsearch.ElasticsearchException as e:
        # maybe handle later...
        raise e

def get_results_dir() -> str:
    if len(sys.argv) < 2:
        print('please enter the results directory',file=sys.stderr)
        exit(-1)
    return sys.argv[1]

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

    #for result in results: 
        #print(result)
        #print("\n"+'_'*80)

    #keys = [time_key, f1_key, pr_key, char_len_key, word_len_key]
    keys = [f1_key, pr_key, time_key]
    names = [key.__name__[:key.__name__.find('_key')] for key in keys]
    return [DescriptiveStats(name,results,key) for name,key in zip(names,keys)]

stats_list: List[Tuple[str,List[DescriptiveStats]]] = []

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

def mean_analysis():
    global stats_list
    directory = get_results_dir()
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

splitter = re.compile('\W')
def calc_recall(base: str, test: str) -> float:
    s_base = set(filter(lambda s: s, splitter.split(base)))
    s_test = set(filter(lambda s: s, splitter.split(test)))
    if len(s_base) == 0 and len(s_test) == 0: return 1
    elif len(s_base) == 0: return 0
    else: return len(s_test.intersection(s_base)) / len(s_base)

def print_(*args):
    with open('results/correlations.txt',mode='a') as file:
        print(*args,file=file)
        print(*args)

def f1_pr_corrcoef_individual(glob_str: str):
    directory = Path(get_results_dir())
    f1s = []
    prs = []
    contexts = []
    prediction_contexts = []
    relevances = []
    for filepath in directory.glob(glob_str):
        with filepath.open() as file:
            results: List[Result] = yaml.full_load(file)
        for result in results:
            f1s.append(f1_key(result))
            prs.append(pr_key(result))
            contexts.append(context_key(result))
            prediction_contexts.append(prediction_context_key(result))
            relevances.append(relevance_key(result))

    recalls = []
    for ctx,pr_ctx in zip(contexts, prediction_contexts):
        recalls.append(calc_recall(ctx,pr_ctx))

    f1s = np.array(f1s)
    prs = np.array(prs)
    recalls = np.array(recalls)

    print_('*'*4)
    print_('*'*4,glob_str, 'mean f1:', f'{np.mean(f1s):5.3f}')
    print_('*'*4,glob_str, 'mean pr:', f'{np.mean(prs):5.3f}')
    print_('*'*4,glob_str, 'mean recall:', f'{np.mean(recalls):5.3f}')
    print_('*'*4,glob_str, 'mean relevance:', f'{np.mean(relevances):5.3f}')
    print_('*'*4)
    print_('*'*4,glob_str, 'Correlation between pr and f1:', f'{np.corrcoef(f1s,prs)[0,1]:5.3f}')
    print_('*'*4,glob_str, 'Correlation between pr and recall:', f'{np.corrcoef(recalls,prs)[0,1]:5.3f}')
    print_('*'*4,glob_str, 'Correlation between f1 and recall:', f'{np.corrcoef(recalls,f1s)[0,1]:5.3f}')
    print_('*'*4,glob_str, 'Correlation between f1 and relevance:', f'{np.corrcoef(relevances,f1s)[0,1]:5.3f}')
    print_('*'*4,glob_str, 'Correlation between pr and relevance:', f'{np.corrcoef(relevances,prs)[0,1]:5.3f}')
    print_('*'*4,glob_str, 'Correlation between relevance and recall:', f'{np.corrcoef(recalls,relevances)[0,1]:5.3f}')
    print_('*'*4)

if __name__ == '__main__':
    mean_analysis()

    f1_pr_corrcoef_individual('*.yml')
    f1_pr_corrcoef_individual('*-1*.yml')
    f1_pr_corrcoef_individual('*-2*.yml')
    f1_pr_corrcoef_individual('*-4*.yml')

