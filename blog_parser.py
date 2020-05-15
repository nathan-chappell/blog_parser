# blog_parser.py

from util import get_log, bannerfy

from html.parser import HTMLParser
from typing import List, Iterable, Tuple, Optional
from typing_extensions import Literal
from datetime import datetime
from fileinput import FileInput

log = get_log(__file__)

def parse_datetime(time: str) -> datetime:
    fmt = '%a, %b %d, %Y' # example: Mon, Jan 1, 2015
    return datetime.strptime(time.strip(), fmt)

# states for the html parser
State = Literal[
    'start',
	'metadata',
	'author',
	'date',
	'article',
    'subtitle',
    'done',
    'error'
    ]

# State Transition Diagram
#
# start ---> metadata <---> author
#                |    <---> date 
#                |
#                ---> article <---> subtitle
#                       |
#                       ---> done

valid_transitions: Iterable[Tuple[State,State]] = set([
    ('start','metadata'),
    ('metadata','author'),
    ('author','metadata'),
    ('metadata','date'),
    ('date','metadata'),
    ('metadata','article'),
    ('article','subtitle'),
    ('subtitle','article'),
    ('article','done'),
])

class ParserError(Exception): pass
Attrs = Iterable[Tuple[str,str]]

class BlogParser(HTMLParser):
    state: State
    fileinput: Optional[FileInput]

    def __init__(self):
        super().__init__()
        self.state = 'start'
        self.fileinput = None

    # basic utilities

    def parse_file(self, filename: str):
        self.fileinput = FileInput([filename])
        log.info(bannerfy(f'begin parsing file: {filename}'))
        for line in self.fileinput:
            self.feed(line)
        log.info(bannerfy(f'done parsing file: {filename}'))

    def location(self) -> str:
        if self.fileinput is not None:
            return f'{self.fileinput.filename()}:{self.fileinput.lineno()}'
        else:
            return "(no location info)"
        
    def transition(self, to_state: State):
        log.info(f"{self.state} -> {to_state} @ {self.location()}")
        if (self.state,to_state) in valid_transitions:
            self.state = to_state
        else:
            log.error('invalid transition')
            log.info(f"{self.state} -> error")
            self.state = 'error'
            raise ParserError('invalid transition')

    # state-machine logic

    def handle_starttag(self, tag: str, attrs: Attrs):
        ...

    def handle_endtag(self, tag: str):
        ...

    def handle_data(self, data: str):
        ...

if __name__ == '__main__':
    b = BlogParser()
    b.transition('metadata')
    b.transition('error')
