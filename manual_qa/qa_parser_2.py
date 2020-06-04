# qa_parser.py

# This parser is meant to parse the questions from chatbot_qa.md.
#
# This is version 2, because now we don't account for multiple answer choices
# to the same question.  Better just keep the old and make a new version than
# completely modifying the old one (just in case we revert back)

import re
import logging
from logging import WARN, DEBUG
from collections import OrderedDict
from typing import Iterable, List, Tuple, Optional, Dict, Set
from itertools import product
from copy import deepcopy
import yaml

from util import is_test, get_logger
from parser_base import LineRes, LineParserBase, GroupDict, State, _State
from parser_result import ParserResult, ParserGreetingSet, ParserQASet

log = get_logger(__file__)

#
# for now, we assume we have a 'line-oriented' ability to parse
HeaderRe = r'^#+\s*(?P<header>.*)\s*'
SectionRe = r'^(?P<section>[A-Z].*)'
GreetingMessageRe = '(?i)\s*\*\*greeting\s*message\*\*\s*'
GreetingRe = '\s*(?P<greeting>[^\s\d#*].*)'
QuestionRe = r'\s*\*\*\s*(?P<question>[^*]*[\S])\s*\*\*\s*'
AnswerRe = '\s*(?P<answer>[^\s\d#*].*)'
EmptyOrAstRe = r'^(?P<line>\s*\**\s*)$'

QALineRes = OrderedDict([
                ('Header',re.compile(HeaderRe)),
                ('Section',re.compile(SectionRe)),
                ('GreetingMessage',re.compile(GreetingMessageRe)),
                ('Greeting',re.compile(GreetingRe)),
                ('Question',re.compile(QuestionRe)),
                ('Answer',re.compile(AnswerRe)),
                ('EmptyOrAst',re.compile(EmptyOrAstRe)),
            ])
### Factor into files...

valid_states = set([
    'title',
    'section',
    'start_greetings',
    'greetings',
    'questions',
    'answers',
])

valid_transitions = {
    'title': ['start_greetings','questions','section'],
    'section': ['start_greetings','questions'],
    'start_greetings': ['greetings'],
    'greetings': ['greetings','questions','section'],
    'questions': ['questions','answers'],
    'answers': ['answers','questions','section'],
}

class QAParser(LineParserBase):
    cur_qa_set: ParserQASet
    # these are necessary while there exists only one answer per question and
    # one greeting per file, and while they span multiple lines...
    cur_answer: List[str]
    cur_greeting: List[str]
    cur_section: str
    result: ParserResult
    state: State
    
    def __init__(self):
        super().__init__(LineRes(QALineRes))
        self.state = State('title',valid_states,valid_transitions)
        self.reset()

    def reset(self):
        self.reset_cur()
        self.result = ParserResult()

    def reset_cur(self):
        self.cur_qa_set = ParserQASet()
        self.cur_answer = []
        self.cur_greeting = []

    def transition(self, next_state: _State):
        self.state.transition(next_state)

    def dispatch(self, title:str, groupdict: GroupDict):
        prev_state = deepcopy(self.state)
        if title == 'GreetingMessage':
            self.transition('start_greetings')
        elif title == 'Greeting':
            self.transition('greetings')
            self.cur_greeting.append(groupdict['greeting'])
        elif title == 'Section':
            self.transition('section')
            self.cur_section = groupdict['section']
            if prev_state == 'answers':
                self.push_cur()
        elif title == 'Question':
            if prev_state == 'answers':
                self.push_cur()
            self.transition('questions')
            self.cur_qa_set.add_question(groupdict['question'])
        elif title == 'Answer':
            self.transition('answers')
            self.cur_answer.append(groupdict['answer'])

    def push_cur(self):
        answer = "\n".join(self.cur_answer).strip()
        self.cur_qa_set.add_answer(answer)
        self.cur_qa_set.metadata['section'] = self.cur_section
        self.result.add_qa_set(self.cur_qa_set)
        if self.cur_greeting:
            greeting = "\n".join(self.cur_greeting).strip()
            self.result.add_greeting(greeting)
        self.reset_cur()

    # 
    # TODO need to return greetings as well...
    # This will be easier when we switch to QASets as well, since then the
    # result of the parse will be a richer data structure anyways
    #
    def parse_file(self, filename: str) -> ParserResult:
        self.reset()
        with open(filename) as file:
            self.feed(file.read())
        self.push_cur()
        return self.result

if __name__ == '__main__':
    log.setLevel(DEBUG)
    filename = 'chatbot_qa_2.md'
    parser = QAParser()
    result = parser.parse_file(filename)
    if is_test():
        print(yaml.dump(result))
    print(yaml.dump(result))
    print(f'total qa sets: {len(result.qa_sets)}')


