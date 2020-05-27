# experiments.py

from util import bannerfy, td2sec, smooth_split

from haystack.reader.transformers import TransformersReader # type: ignore
from haystack.database.base import Document # type: ignore

import yaml
import re
from datetime import datetime
from typing import List, Union, Dict, Any

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


def print_result(result: Result,pretty_file=None,yaml_file=None,out=False):
    br = "\n" + "-"*40 + "\n"
    pretty = str(result) + br
    if out: print(pretty)
    if pretty_file: print(pretty,file=pretty_file)
    if yaml_file: print(yaml.dump([result]),file=yaml_file,flush=True)

def rough_f1(l: str, r: str) -> float:
    splitter = re.compile('\W')
    sl = set(splitter.split(l)) - set([''])
    sr = set(splitter.split(r)) - set([''])
    inter = sl.intersection(sr)
    return 2.*len(inter) / (len(sr) + len(sl))

def run_sample(sample: Dict[str,Any], documents: List[Document], reader: TransformersReader) -> Result:
    question = sample['question']
    answer = sample['answer']
    context = document.text
    result = Result(question, answer, context)
    split = datetime.now()
    predictions = reader.predict(question, documents)
    result.time = td2sec(datetime.now() - split)
    for p in predictions['answers']:
        result.add_prediction(p)
    return result

if __name__ == '__main__':
    reader = TransformersReader()

    pretty_filename = 'initial_results_pretty.txt'
    pretty_file = open(pretty_filename,mode='w')
    yaml_filename = 'initial_results.yml'
    yaml_file = open(yaml_filename,mode='w')

    results = []

    samples_filename = 'samples.yml'
    with open(samples_filename) as file:
        samples = yaml.full_load(file)

    import os
    if 'EXPERIMENTS_TEST' in os.environ.keys():
        TEST_RUN = True
    else:
        TEST_RUN = False

    if TEST_RUN:
        print(bannerfy(__file__ + ' TEST RUN'))
        _samples = samples[:3]
    else:
        _samples = samples

    n = len(_samples)

    inc = .2
    status = inc
    for i,sample in enumerate(_samples):
        document = Document(
            id='X', 
            text=sample['context'],
            external_source_id=None, 
            question=None, 
            query_score=None, 
            meta=None,
        )
        result = run_sample(sample, [document], reader=reader)
        results.append(result)
        print_result(result,pretty_file,yaml_file)
        if (i / n > status):
            status += inc
            pct = round(i/n*100)
            print(bannerfy(f'{pct}% complete'))

    print(bannerfy(f'100% complete'))
    yaml_file.close()
    pretty_file.close()
