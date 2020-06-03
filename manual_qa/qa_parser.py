# qa_parser.py

# This parser is meant to parse the questions from chatbot_qa.md.

import re
import logging
from logging import WARN, DEBUG
from pprint import pprint
from collections import OrderedDict
from typing import Iterable, List, Tuple, Optional, Dict
from itertools import product
import sys
import yaml

from util import is_test, get_logger

log = get_logger(__file__)

#
# for now, we assume we have a 'line-oriented' ability to parse
ws = r'\s*'
dast = r'\*\*'
HeaderRe = r'^#+' + ws + '(?P<name>.*)' + ws
SectionRe = r'^(?P<name>[A-Z].*)'
QuestionRe = r'[^*]*'+dast+ws+'(?P<question>.*\?)'+ws+dast+ws
QuestionNumberRe = r'^' + ws + r'(?P<number>\d+)\.' + QuestionRe
AnswerRe = r'^(?:\W*[a-z]\)\W*|\s+)(?P<answer>\w.*)'

QALineRes = OrderedDict([
                ('Header',re.compile(HeaderRe)),
                ('Section',re.compile(SectionRe)),
                ('QuestionNumber',re.compile(QuestionNumberRe)),
                ('Question',re.compile(QuestionRe)),
                ('Answer',re.compile(AnswerRe)),
            ])

GroupDict = Dict[str,str]

class LineRes:
    res: OrderedDict

    def __init__(self, res: OrderedDict):
        self.res = res

    def __call__(self, line: str) -> Optional[Tuple[str,GroupDict]]:
        for title, r in self.res.items():
            m = r.match(line)
            if m: return (title, m.groupdict())
        return None

class LineParserBase:
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
            if line.strip():
                log.debug(f'line {i:3} {line}')
                log.debug(f'line {i:3} {res}')
            if not res: continue
            elif isinstance(res,tuple):
                title, groupdict = res
                self.dispatch(title,groupdict)
            self.dispatch('Newline',{})

    def dispatch(self, title: str, groupdict: GroupDict):
        ...

class QAPair(yaml.YAMLObject):
    yaml_tag = u'!QAPair'

    question: str
    answer: str
    number: str

    def __init__(self, t: Tuple[str,str]):
        self.question = t[0]
        self.answer = t[1]

class QAParser(LineParserBase):
    cur_qs: List[str]
    cur_as: List[str]
    cur_no: str
    qa_pairs: List[QAPair]
    
    def __init__(self):
        super().__init__(LineRes(QALineRes))
        self.reset()

    def push_cur(self):
        try:
            if self.cur_qs or self.cur_as: assert self.cur_qs and self.cur_as
            self.qa_pairs.extend(map(QAPair, product(self.cur_qs,self.cur_as,[self.cur_no])))
            self.reset_cur()
        except AssertionError as e:
            if not self.cur_qs:
                log.warn(f'No current question to push: cur_no {self.cur_no}')
            elif not self.cur_as:
                log.warn(f'No current answer to push: cur_no {self.cur_no}')
            else:
                raise RuntimeError('not reachable')
            if is_test(): 
                raise e


    def dispatch(self, title:str, groupdict: GroupDict):
        if title == 'QuestionNumber':
            self.push_cur()
            self.cur_no = groupdict['number']
            self.cur_qs.append(groupdict['question'])
        elif title == 'Question':
            self.cur_qs.append(groupdict['question'])
        elif title == 'Answer':
            self.cur_as.append(groupdict['answer'])

    def reset(self):
        self.reset_cur()
        self.qa_pairs = []
        self.cur_no = ''

    def reset_cur(self):
        self.cur_qs = []
        self.cur_as = []

    def parse_file(self, filename: str) -> List[QAPair]:
        self.reset()
        with open(filename) as file:
            self.feed(file.read())
        if not is_test():
            self.push_cur()
        return self.qa_pairs

if __name__ == '__main__':
    filename = 'chatbot_qa.md'
    parser = QAParser()
    qa_pairs = parser.parse_file(filename)
    if is_test():
        print(yaml.dump(qa_pairs))
    print(f'total qa pairs: {len(qa_pairs)}')


