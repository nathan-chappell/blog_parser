# qa_parser.py

# This parser is meant to parse the questions from chatbot_qa.md.

import re
import logging
from logging import WARN, DEBUG
from pprint import pprint
from collections import OrderedDict
from typing import Iterable, List, Tuple, Optional, Dict, Set, Generator
from itertools import product
import sys
import yaml

from util import is_test, get_logger

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

GroupDict = Dict[str,str]

class StateError(Exception): pass
class StateTransitionError(StateError): pass

_State = str

class State:
    _valid_states: Set[_State]
    _valid_transitions: Dict[_State,List[_State]]
    _state: _State

    def __init__(
            self,
            initial_state: _State,
            valid_states: Set[_State],
            valid_transitions: Dict[_State,List[_State]],
            ):
        if initial_state not in valid_states:
            raise StateError('initial state must be valid')
        all_states = set([initial_state])
        all_states.update(valid_transitions.keys())
        for rhs in valid_transitions.values():
            all_states.update(rhs)
        if not all_states.issubset(valid_states):
            invalid_states = all_states - valid_states
            raise StateError('invalid states: ' + ', '.join(invalid_states))
        self._state = initial_state
        self._valid_states = valid_states
        self._valid_transitions = valid_transitions

    def is_valid_state(self, state: _State) -> bool:
        return state in self._valid_states
        
    def is_valid_transition(self, l: _State, r: _State) -> bool:
        return all([
                self.is_valid_state(l),
                self.is_valid_state(r),
                r in self._valid_transitions.get(l,[])
                ])

    def transition(self, next_state: _State):
        if not self.is_valid_state(next_state):
            raise StateError(f'next_state is invalid: {next_state}')
        if not self.is_valid_transition(self._state, next_state):
            raise StateTransitionError(
                f'invalid transition: {self._state} -> {next_state}'
            )
        log.debug(f'{self._state} -> {next_state}')
        self._state = next_state

    def __eq__(self, state: object) -> bool:
        if isinstance(state, _State):
            if not self.is_valid_state(state):
                raise StateError(f'Comparison with invalid state: {state}')
            return self._state == state
        raise StateError('State comparison against not _State [str]')

    def __repr__(self) -> str:
        return f'State({self._state})'


class LineRes:
    res: OrderedDict

    def __init__(self, res: OrderedDict):
        self.res = res

    #def __call__(self, line: str) -> Optional[Tuple[str,GroupDict]]:
    def __call__(self, line: str) -> Generator[Tuple[str,GroupDict],None,None]:
        """Iterate through our resolvers until we exhaust them or
           successfully cause a state transition
        """
        for title, r in self.res.items():
            m = r.match(line)
            if m is None:
                continue
            yield (title, m.groupdict())

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
            i = i+1
            res_gen = lineRes(line)
            try: 
                while True:
                    res = res_gen.__next__()
                    if line.strip():
                        log.debug(f'line {i:3} {line}')
                        log.debug(f'line {i:3} {res}')
                    try:
                        title, groupdict = res
                        self.dispatch(title,groupdict)
                        res_gen.throw(StopIteration)
                    except StateTransitionError:
                        continue
                    except StopIteration:
                        break
            except StopIteration:
                log.error(f'No valid resolution for line: {i}')
                raise Exception('Parser Error')
            except:
                log.error(f'Parser error occured at line: {i}')
                raise

    def dispatch(self, title: str, groupdict: GroupDict):
        ...

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


