# parser_result.py

import yaml
import random
from typing import List, Set, Dict, Any

from util import get_logger

log = get_logger(__file__)

class ParserResultMeta(type):
    """Metaclass for results classes."""

    def __new__(cls,name,bases,dict_):
        yaml_tag = f'!ParserResult_{name}'
        dict_['yaml_tag'] = yaml_tag
        def repr(self):
            return yaml.dump(self)
        dict_['__repr__'] = repr
        bases = bases + (yaml.YAMLObject,)
        return type(name,bases,dict_)

class ParserQASet(metaclass=ParserResultMeta):
    questions: Set[str]
    # for now this will always have exactly one element.
    # hopefully we can change that.
    answers: Set[str]
    metadata: Dict[str,Any]

    def __init__(self):
        self.questions = set()
        self.answers = set()
        # maybe we'll use this for categorization or more advanced scoring
        # techniques...
        self.metadata = {}

    def add_question(self, question:str):
        self.questions.add(question)

    def add_answer(self, answer:str):
        self.answers.add(answer)

    def get_random_answer(self) -> str:
        return random.choice(list(self.answers))


class ParserGreetingSet(metaclass=ParserResultMeta):
    # for now this will always have exactly one element.
    # hopefully we can change that.
    greetings: Set[str]

    def __init__(self):
        self.greetings = set()

    def add_greeting(self, greeting: str):
        self.greetings.add(greeting)

    def get_random_greeting(self) -> str:
        return random.choice(list(self.greetings))

class ParserResult(metaclass=ParserResultMeta):
    qa_sets: List[ParserQASet]
    greeting_set: ParserGreetingSet

    def __init__(self):
        self.qa_sets = []
        self.greeting_set = ParserGreetingSet()

    def add_qa_set(self, qa_set: ParserQASet):
        if self.verify_qa_set(qa_set):
            self.qa_sets.append(qa_set)
        else:
            log.warn('bad qa set, not adding to list')
            log.info(qa_set)

    def add_greeting(self, greeting: str):
        self.greeting_set.add_greeting(greeting)

    def verify_qa_set(self, qa_set: ParserQASet):
        is_valid = True
        if not qa_set.questions:
            log.warn('invalid qa_set: no questions')
            is_valid = False
        if not qa_set.answers:
            log.warn('invalid qa_set: no answers')
            is_valid = False
        return is_valid
