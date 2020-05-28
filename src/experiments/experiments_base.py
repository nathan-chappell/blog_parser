# experiments_base.py

import yaml
import re
from typing import List, Union, Dict, Any, Iterable
from datetime import datetime

#
# needed to import from ../util.py
# 
def add_parent_dir_to_path():
    from pathlib import Path
    import sys
    parent = str((Path() / '..').resolve())
    sys.path.append(parent)

add_parent_dir_to_path()

from util import smooth_split, bannerfy # type: ignore

samples_filename = 'yml_samples.yml'
results_dir = './results'

#
# the dumb status bar is ugly, but informative.
# tqdm is out, because another library is using it, and in general using a
# pretty status bar won't work well cause I'm expecting other stuff to be
# printing out as well
#
def dumbStatusBar(stuff: Iterable, name: str = "_"):
    inc = .2
    status = inc
    n = len(stuff)
    for i,thing in enumerate(stuff):
        if i/n > status:
            print(bannerfy(f'{name} {100*i/n:5.2f}% complete'))
            status += inc
        yield thing

class Prediction(yaml.YAMLObject):
    yaml_tag = u'!Prediction'

    pr: float # ... probability
    f1: float
    answer: str

    def __init__(self,pr,f1,answer):
        self.pr = pr
        self.f1 = f1
        self.answer = answer

    def __repr__(self) -> str:
        return yaml.dump(self)

    def __str__(self) -> str:
        pr = f'pr: {self.pr:5.3f}'
        f1 = f'f1: {self.f1:5.3f}'
        #a =  f'answer: {self.answer}'
        a =  f'{self.answer}'
        return f'{a} | ' + ', '.join([pr,f1])

class Result(yaml.YAMLObject):
    yaml_tag = u'!Result'

    question: str
    answer: str
    context: str
    predictions: List[Prediction]
    time: float

    def __init__(self,question,answer,context):
        self.question = question
        self.answer = answer
        self.context = context
        self.predictions = []

    def add_prediction(self,prediction: Union[Prediction,Dict[str,Any]]):
        if isinstance(prediction,Prediction):
            self.predictions.append(prediction)
        else:
            _answer = prediction['answer']
            _f1 = rough_f1(self.answer, _answer)
            _pr = prediction['probability']
            self.predictions.append(Prediction(_pr,_f1,_answer))

    def __repr__(self) -> str:
        return yaml.dump(self)
    
    def __str__(self) -> str:
        w = 20
        fmt = f"{{s:{w}}}| "
        result = []
        result.append(fmt.format(s='question:') + self.question)
        result.append(fmt.format(s='my answer:') + self.answer)
        result.append('.'*w)
        for prediction in self.predictions:
            result.append(fmt.format(s='prediction') + str(prediction))
        result.append('.'*w)
        result.append(fmt.format(s='time') + f'{self.time:5.3f}')
        aligned_context = ("\n" + w*' ').join(smooth_split(self.context,80-w))
        result.append(fmt.format(s='context') + aligned_context)
        return "\n".join(result)

class Sample(yaml.YAMLObject):
    yaml_tag = u'!Sample'

    question: str
    answer: str
    context: str
    filename: str
    article_title: str

def print_multi(item: Any, pretty_file=None, yaml_file=None, out=False):
    br = "\n" + "-"*40 + "\n"
    pretty = str(item) + br
    if out: print(pretty)
    if pretty_file: print(pretty,file=pretty_file)
    if yaml_file: print(yaml.dump([item]),file=yaml_file,flush=True)

def rough_f1(l: str, r: str) -> float:
    splitter = re.compile('\W')
    sl = set(splitter.split(l)) - set([''])
    sr = set(splitter.split(r)) - set([''])
    inter = sl.intersection(sr)
    return 2.*len(inter) / (len(sr) + len(sl))

class ExperimentBase:
    name: str
    description: str
    print_out: bool

    def __init__(self, name=None, description=None, print_out=True):
        if name:
            self.name = name
        else:
            self.name = self.__class__.__name__
        if description:
            self.description = description
        elif self.__class__.__doc__:
            self.self.__class__.__doc__ = self.__class__.__doc__
        else:
            self.description = "no description"
        self.print_out = print_out

    def get_samples() -> List[Sample]:
        with open(yml_samples) as file:
            samples = yaml.full_load(file.read())
        return samples

    def prepare(self):
        ...

    #
    # just get the result, time is kept in run_experiment()
    #
    def handle_sample(self, Sample) -> Result:
        raise NotImplementedError
    
    def run_experiment(self):
        samples = self.get_samples()
        yaml_file = open(results_dir + '/' + self.name + '.yml')
        pretty_file = open(results_dir + '/' + self.name + '.txt')
        welcome = f"Experiment: {self.name}\nDescription: {self.description}"
        print_multi(bannerfy(welcome,banner_char="#"))
        for sample in dumbStatusBar(samples):
            split = datetime.now()
            result = self.handle_sample(sample)
            time = td2sec(datetime.now()-split)
            result.time = time
            print_multi(result, yaml_file, pretty_file, self.print_out)

