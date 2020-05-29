# experiments_base.py

import yaml
import re
from typing import List, Union, Dict, Any, Sequence
from datetime import datetime
from logging import DEBUG, INFO
from functools import lru_cache
import os

#
# needed to import from ../util.py
# 
def add_parent_dir_to_path() -> None:
    from pathlib import Path
    import sys
    parent = str((Path() / '..').resolve())
    sys.path.append(parent)

add_parent_dir_to_path()

from util import smooth_split, bannerfy, get_log, td2sec # type: ignore

yml_samples = 'yml_samples.yml'
log = get_log(__file__)
log.setLevel(INFO)

def is_test_run() -> bool:
    test = os.environ.get('EXPERIMENTS_TEST','false')
    return test.lower() == 'true'

# cache used to keep timestamp for entire program run

_now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def get_results_files(name: str):
    import atexit
    from pathlib import Path
    if is_test_run():
        results_dir = Path('results') / f'test-{_now}'
    else:
        results_dir = Path('results') / _now
    if not results_dir.exists(): results_dir.mkdir(parents=True)
    pretty_path = results_dir / f'{name}_pretty.txt'
    yaml_path = results_dir / f'{name}.yml'
    pretty_file = open(pretty_path, 'w')
    yaml_file = open(yaml_path, 'w')
    def close_files():
        pretty_file.close()
        yaml_file.close()
    atexit.register(close_files)
    return pretty_file, yaml_file

#
# the dumb status bar is ugly, but informative.
# tqdm is out, because another library is using it, and in general using a
# pretty status bar won't work well cause I'm expecting other stuff to be
# printing out as well
#
def dumbStatusBar(stuff: Sequence, name: str = "_"):
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
    metadata: Dict[str,str]

    def __init__(self,pr,f1,answer,metadata={}):
        self.pr = pr
        self.f1 = f1
        self.answer = answer
        self.metadata = metadata

    def __repr__(self) -> str:
        return yaml.dump(self)

    def __str__(self) -> str:
        pr = f'pr: {self.pr:5.3f}'
        f1 = f'f1: {self.f1:5.3f}'
        #a =  f'answer: {self.answer}'
        a =  f'{self.answer}'
        #return f'{a} | ' + ', '.join([pr,f1])
        return ', '.join([f1,pr]) + ' | ' + a

class Sample(yaml.YAMLObject):
    yaml_tag = u'!Sample'

    question: str
    answer: str
    context: str
    filename: str
    article_title: str

class Result(yaml.YAMLObject):
    yaml_tag = u'!Result'

    question: str
    answer: str
    context: str
    predictions: List[Prediction]
    time: float
    experiment_name: str

    def __init__(self,question,answer,context,experiment_name):
        self.question = question
        self.answer = answer
        self.context = context
        self.predictions = []
        self.experiment_name = experiment_name

    # factory
    @staticmethod
    def from_sample(sample: Sample) -> 'Result':
        return Result(
            sample.question,
            sample.answer,
            sample.context,
            'from_sample', # this should be changed upon receipt
        )

    def add_prediction(
            self,
            prediction: Union[Prediction,Dict[str,Any]],
            additional_metadata: Dict[str,Any] = {}
        ):
        #import pdb
        #pdb.set_trace()
        if isinstance(prediction,Prediction):
            self.predictions.append(prediction)
        else:
            _answer = prediction['answer']
            _f1 = rough_f1(self.answer, _answer)
            _pr = prediction['probability']
            _metadata = prediction.get('meta',{})
            _metadata.update(additional_metadata)
            self.predictions.append(Prediction(_pr,_f1,_answer,_metadata))

    def __repr__(self) -> str:
        return yaml.dump(self)
    
    def __str__(self) -> str:
        w = 20
        fmt = f"{{s:{w}}}| "
        result = []
        result.append(fmt.format(s='experiment:') + self.experiment_name)
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

# 
# yaml_file is now deprecated...
# aliases are screwing up our hack-job
#
def print_multi(item: Any, pretty_file=None, yaml_file=None):
    br = "\n" + "-"*40 + "\n"
    pretty = str(item) + br
    log.info(pretty)
    if pretty_file: print(pretty,file=pretty_file)
    assert yaml_file is None
    #if yaml_file: print(yaml.dump([item]),file=yaml_file,flush=True)

def rough_f1(l: str, r: str) -> float:
    splitter = re.compile('\W')
    sl = set(splitter.split(l)) - set([''])
    sr = set(splitter.split(r)) - set([''])
    inter = sl.intersection(sr)
    return 2.*len(inter) / (len(sr) + len(sl))

class ExperimentBase:
    name: str
    description: str
    yml_samples: str
    # test_run makes run_experiment only run against two samples
    test_run: bool = False

    def __init__(self, name=None, description=None, print_out=True):
        if name:
            self.name = name
        else:
            self.name = self.__class__.__name__
        if description:
            self.description = description
        elif self.__class__.__doc__:
            self.description = self.__class__.__doc__
        else:
            self.description = "no description"
        self.yml_samples = yml_samples

    def get_samples(self) -> List[Sample]:
        with open(self.yml_samples) as file:
            samples = yaml.full_load(file.read())
        return samples

    def prepare(self):
        pass

    #
    # just get the result, time is kept in run_experiment()
    #
    def handle_sample(self, Sample) -> Result:
        raise NotImplementedError
    
    def run_experiment(self) -> None:
        import re
        samples = self.get_samples()
        if self.test_run: samples = samples[0:2]
        pretty_file, yaml_file = get_results_files(self.name)
        name = f"Experiment: {self.name}"
        description = re.sub('\s+',' ',f"Description: {self.description}")
        print_multi(bannerfy(f"{name}\n{description}",banner_char="#"),pretty_file,None)
        results = []
        for sample in dumbStatusBar(samples):
            split = datetime.now()
            result = self.handle_sample(sample)
            time = td2sec(datetime.now()-split)
            result.time = time
            results.append(result)
            print_multi(result, pretty_file, None)
        print(yaml.dump(results),file=yaml_file)

