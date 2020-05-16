# machine_html_parser.py

from util import get_log, bannerfy

from html.parser import HTMLParser
from typing import Iterable, List, Tuple, Optional
from typing_extensions import Literal
import re

Attrs = Iterable[Tuple[str,Optional[str]]]
Event = Literal['starttag','endtag','DATA']
TagOrData = str
State = str

log = get_log(__file__,stderr=True)

class ParserError(Exception): pass
class ValidatorError(Exception): pass

#
# convenience class for comparing machine states
#
class TransitionData:
    state: State
    tagOrData: TagOrData
    event: Event

    def __init__(self, state: State, tagOrData: TagOrData, event: Event):
        self.state = state
        self.tagOrData = tagOrData
        self.event = event

    #
    # this just makes comparison with tuples easier...
    #
    def __iter__(self):
        return iter((self.state,self.tagOrData,self.event))

    @staticmethod
    def str_comp(l,r):
        res = l == r or l == '*' or r == '*'
        res = res or re.match(l,r) or re.match(r,l)
        return res

    def __eq__(self, other: object):
        try:
            comp = TransitionData.str_comp
            return all([comp(l,r) for l,r in zip(self, other)]) # type: ignore
        except TypeError:
            return False

class MachineHTMLParser(HTMLParser):
    state: State

    def __init__(self):
        super().__init__()

    # state-machine logic

    def reset(self):
        super().reset()

    def dispatch(self, ms: TransitionData, attrs: Attrs={}):
        raise NotImplementedError

    def validate_transition(self, to_state: State):
        raise NotImplementedError

    # basic utilities

    def parse_file(self, filename: str):
        self.filename = filename
        log.info(bannerfy(f"begin parsing file:\n{filename}"))
        with open(filename) as file:
            self.feed(file.read())
        log.info(bannerfy(f"done parsing file:\n{filename}"))

    def location(self) -> str:
        line, offset = self.getpos()
        return f'{self.filename}:{line}:{offset}'
        
    def transition(self, to_state: State):
        log.info(f"{self.state:<10} -> {to_state:<10} @ {self.location()}")
        try:
            if self.validate_transition(to_state):
                self.state = to_state
            else:
                raise ParserError('invalid transition')
        except ParserError as e:
            log.error(e)
            log.info(f"{self.state} -> error")
            self.state = 'error'

    # Events from base class.  These are all routed through dispatch()
    
    def handle_starttag(self, tag: str, attrs: Attrs):
        self.dispatch(TransitionData(self.state,tag,'starttag'),attrs=attrs)

    def handle_endtag(self, tag: str):
        self.dispatch(TransitionData(self.state,tag,'endtag'))

    def handle_data(self, data: str):
        self.dispatch(TransitionData(self.state,data,'DATA'))


