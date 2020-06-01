# qa_parser.py

# This parser is meant to parse the questions from chatbot_qa.md.

import re
import logging
from logging import WARN, DEBUG
from pprint import pprint
from collections import OrderedDict
from typing import Iterable, List, Tuple, Optional, Dict
from itertools import product
import os
import sys
import yaml

def is_test():
    return os.environ.get('TEST',False)

if sys.version_info >= (3,8):
    from typing import Literal
else:
    from typing_extensions import Literal

log = logging.getLogger(__file__)
formatter = logging.Formatter('%(name)s %(funcName)s %(levelname)s %(message)s')
handlers = [
        logging.FileHandler('parser.log'),
        logging.StreamHandler()
]
for handler in handlers: 
    handler.setFormatter(formatter)
    log.addHandler(handler)

if is_test():
    log.setLevel(DEBUG)
else:
    log.setLevel(WARN)

#
# for now, we assume we have a 'line-oriented' ability to parse

QALineRes = OrderedDict([
                ('HeaderName',re.compile(r'^#+\s*(?P<HeaderName>.*)')),
                ('HeaderNameAlt',re.compile(r'^(?P<HeaderNameAlt>[A-Z].*)')),
                ('QuestionNumber',re.compile(r'^(?P<QuestionNumber>\d+)\.')),
                ('Question',re.compile(r'[^*]*\*\*(?P<Question>.*\?)\*\*')),
                ('Answer',re.compile(r'^(?:\W+(?:[a-z]\))\W*|\s+(?=[^\*]))(?P<Answer>.*)')),
            ])

class LineRes:
    res: OrderedDict

    def __init__(self, res: OrderedDict):
        self.res = res

    def __call__(self, line: str) -> OrderedDict:
        matches: OrderedDict = OrderedDict({})
        for title, r in self.res.items():
            m = r.match(line)
            if m: matches.update({title: m[title].strip()})
        return matches

class ParserBase:
    lineRes: LineRes

    def __init__(self, lineRes: LineRes):
        self.lineRes = lineRes

    def feed(self, data: str):
        lines: List[str] = data.split("\n")
        if is_test(): lines = lines[0:30]
        lineRes = self.lineRes
        log.debug(f'parsing {len(lines)} lines')
        for i,line in enumerate(lines):
            res = lineRes(line)
            log.debug(f'line {i:3} {res}')
            if not res: continue
            for k,v in res.items():
                # here we'll depart from the html parser and call dispatch
                # directly...
                self.dispatch(k,v)
            self.dispatch('Newline','')

    def dispatch(self,k: str, v: str):
        ...

class QAPair(yaml.YAMLObject):
    yaml_tag = u'!QAPair'

    question: str
    answer: str

    def __init__(self, t: Tuple[str,str]):
        self.question = t[0]
        self.answer = t[1]

class QAParser(ParserBase):
    cur_qs: List[str]
    cur_as: List[str]
    qas: List[QAPair]
    
    def __init__(self):
        super().__init__(LineRes(QALineRes))
        self.reset()

    def push_cur(self):
        self.qas.extend(map(QAPair,product(self.cur_qs,self.cur_as)))
        self.reset_cur()

    def dispatch(self, k:str, v:str):
        if k == 'QuestionNumber':
            self.push_cur()
        elif k == 'Question':
            self.cur_qs.append(v)
        elif k == 'Answer':
            self.cur_as.append(v)

    def reset(self):
        self.reset_cur()
        self.qas = []

    def reset_cur(self):
        self.cur_qs = []
        self.cur_as = []

    def parse_file(self, filename: str) -> List[QAPair]:
        self.reset()
        with open(filename) as file:
            self.feed(file.read())
        self.push_cur()
        return self.qas

if __name__ == '__main__':
    filename = 'chatbot_qa.md'
    parser = QAParser()
    qas = parser.parse_file(filename)
    print(yaml.dump(qas))

