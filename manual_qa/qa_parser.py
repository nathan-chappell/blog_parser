# qa_parser.py

# This parser is meant to parse the questions from chatbot_qa.md.

import re
import logging
from logging import WARN, DEBUG
from pprint import pprint
from collections import OrderedDict
from typing import Iterable, List, Tuple, Optional, Dict, Set
from itertools import product
import sys
import yaml

from util import is_test, get_logger
from parser_base import LineRes, LineParserBase, GroupDict, State, _State

log = get_logger(__file__)

#
# for now, we assume we have a 'line-oriented' ability to parse
nocase = r'(?i)'
ws = r'\s*'
dast = r'\*\*'
HeaderRe = r'^#+' + ws + '(?P<name>.*)' + ws
SectionRe = r'^(?P<name>[A-Z].*)'
GreetingMessageRe = nocase+ws+dast+ws+'greeting'+ws+'message'+ws+dast+ws
GreetingRe = ws+'(?P<greeting>[^\s\d#*].*)'
#QuestionRe = r'[^*]*'+dast+ws+'(?P<question>.*\?)'+ws+dast+ws
QuestionRe = r'[^*]*'+dast+ws+'(?P<question>.*\S)'+ws+dast+ws
QuestionNumberRe = r'^' + ws + r'(?P<number>\d+)\.' + QuestionRe
AnswerRe = r'^(?:\W*[a-z]\)\W*|\s+)(?P<answer>[\w\[].*)'
EmptyRe = r'^(?P<line>\s*\**\s*)$'

QALineRes = OrderedDict([
                ('Header',re.compile(HeaderRe)),
                ('Section',re.compile(SectionRe)),
                ('GreetingMessage',re.compile(GreetingMessageRe)),
                ('Greeting',re.compile(GreetingRe)),
                ('QuestionNumber',re.compile(QuestionNumberRe)),
                ('Question',re.compile(QuestionRe)),
                ('Answer',re.compile(AnswerRe)),
                ('Empty',re.compile(EmptyRe)),
            ])

#
# TODO go from parsing these pairs to parsing QA sets...
#
class QAPair(yaml.YAMLObject):
    yaml_tag = u'!QAPair'

    question: str
    answer: str
    number: str

    def __init__(self, t: Tuple[str,str]):
        self.question = t[0]
        self.answer = t[1]

    def __repr__(self) -> str:
        return yaml.dump(self)

class Greeting(yaml.YAMLObject):
    yaml_tag = u'!GreetingMessage'
    messages: List[str]

    def __init__(self, messages: List[str] = []):
        self.messages = messages

### Factor into files...

valid_states = set([
    'title',
    'start_greetings',
    'greetings',
    'start_questions',
    'questions',
    'answers',
])

valid_transitions = {
    'title': ['start_greetings','start_questions'],
    'start_greetings': ['greetings','start_questions'],
    'greetings': ['greetings','start_questions'],
    'start_questions': ['questions','answers'],
    'questions': ['questions','answers'],
    'answers': ['answers','start_questions'],
}

class QAParser(LineParserBase):
    cur_qs: List[str]
    cur_as: List[str]
    cur_no: str
    qa_pairs: List[QAPair]
    greeting: Greeting
    state: State
    
    def __init__(self):
        super().__init__(LineRes(QALineRes))
        self.state = State('title',valid_states,valid_transitions)
        self.reset()

    def push_cur(self):
        try:
            if self.cur_qs or self.cur_as: assert self.cur_qs and self.cur_as
            all_pairs = map(QAPair, 
                            product(self.cur_qs,self.cur_as,[self.cur_no]))
            self.qa_pairs.extend(all_pairs)
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
        if title == 'GreetingMessage':
            self.transition('start_greetings')
        elif title == 'Greeting':
            self.transition('greetings')
            self.greeting.messages.append(groupdict['greeting'])
        elif title == 'QuestionNumber':
            self.transition('start_questions')
            self.push_cur()
            self.cur_no = groupdict['number']
            self.cur_qs.append(groupdict['question'])
        elif title == 'Question':
            self.transition('questions')
            self.cur_qs.append(groupdict['question'])
        elif title == 'Answer':
            self.transition('answers')
            self.cur_as.append(groupdict['answer'])

    def transition(self, next_state: _State):
        self.state.transition(next_state)

    def reset(self):
        self.reset_cur()
        self.qa_pairs = []
        self.greeting = Greeting()
        self.cur_no = ''

    def reset_cur(self):
        self.cur_qs = []
        self.cur_as = []

    # 
    # TODO need to return greetings as well...
    # This will be easier when we switch to QASets as well, since then the
    # result of the parse will be a richer data structure anyways
    #
    def parse_file(self, filename: str) -> List[QAPair]:
        self.reset()
        with open(filename) as file:
            self.feed(file.read())
        if not is_test():
            self.push_cur()
        return self.qa_pairs

if __name__ == '__main__':
    log.setLevel(DEBUG)
    filename = 'chatbot_qa_1.md'
    parser = QAParser()
    qa_pairs = parser.parse_file(filename)
    if is_test():
        print(yaml.dump(qa_pairs))
    print(f'total qa pairs: {len(qa_pairs)}')
    print(yaml.dump(qa_pairs))


