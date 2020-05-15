# blog_parser.py

from util import get_log, bannerfy

from html.parser import HTMLParser
from typing import List, Iterable, Tuple, Optional, Union, FrozenSet, Dict
from typing import Callable
from typing_extensions import Literal
from datetime import datetime
from pprint import pprint, pformat
import json

log = get_log(__file__)

def parse_date(time: str) -> str:
    fmt = '%a, %b %d, %Y' # example: Mon, Jan 1, 2015
    return datetime.strptime(time.strip(), fmt).isoformat()

#
# states for the html parser
#
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

Attrs = Iterable[Tuple[str,Optional[str]]]
TagOrData = str
Event = Literal['starttag','endtag','DATA']

# convenience class for comparing machine states

class MachineState:
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
    def str_comp_wildcard(l,r):
        return l == r or l == '*' or r == '*'

    def __eq__(self, other: object):
        try:
            comp = MachineState.str_comp_wildcard
            return all([comp(l,r) for l,r in zip(self, other)]) # type: ignore
        except TypeError:
            return False

#
# unit of information eaten by BlogParser
#
class Paragraph:
    metadata: Dict[str,str]
    text: str

    attrs: FrozenSet[str] = frozenset([
        "author",
        "date",
        "article_title",
        "paragraph_title",
        "filename",
    ])

    def __init__(self):
        self._set_metadata({k:"" for k in Paragraph.attrs})

    def __setattr__(self,k,v):
        metadata_access_err_msg = bannerfy("""
Please access Paragraph.metadata by assigning metadata directly, e.g:
>>> p = Paragraph()
>>> p.author = Kurt Vonnegut
""")
        if k in attrs: self.metadata[k]= v
        elif k == 'text': object.__setattr__(self,k,v)
        elif k == 'metadata': raise KeyError(metadata_access_err_msg)
        else: raise KeyError(f"{k} not a recognized attribute")

    def __getattr__(self,k):
        if k == 'text':
            return object.__getattr__(self,k)
        if k in Paragraph.attrs:
            return object.__getattr__(self,'metadata')[k]
        else:
            raise KeyError(f"{k} not a recognized attribute")

    def __repr__(self) -> str:
        return json.dumps({"metadata":self.metadata.copy(),"text":self.text})

    def __str__(self) -> str:
        text = f'{self.text[0:20]}... length: {len(self.text)}'
        return json.dumps({"metadata":self.metadata.copy(),"text":text})

    #
    # returns a new paragraph with copied metadata except paragraph_title
    # and blank text field
    #
    def new_paragraph(self) -> Paragraph:
        p = Paragraph()
        p._set_metadata(self.metadata.copy())
        p.paragraph_title = ""
        return p

    def _set_metadata(self, metadata: Dict[str,str]):
        object.__setattr__(self,'metadata',metadata)

ParagraphAction = Callable[[Paragraph],None]

def default_paragraph_action(paragraph: Paragraph):
    pprint(paragraph,indent=2)
    log.info(str(paragraph),indent=2)

class BlogParser(HTMLParser):
    state: State
    paragraph_action: Callable[[Paragraph],None]
    paragraph: Paragraph

    def __init__(self,paragraph_action = default_paragraph_action):
        super().__init__()
        self.paragraph_action = paragraph_action
        self.paragraph = Paragraph()

    def reset(self):
        super().reset()
        self.state = 'start'

    # basic utilities

    def parse_file(self, filename: str):
        self.paragraph.filename = filename
        log.info(bannerfy(f'begin parsing file: {filename}'))
        with open(filename) as file:
            self.feed(file.read())
        log.info(bannerfy(f'done parsing file: {filename}'))

    def location(self) -> str:
        line, offset = self.getpos()
        return f'{self.paragraph.filename}:{line}:{offset}'
        
    def transition(self, to_state: State):
        log.info(f"{self.state} -> {to_state} @ {self.location()}")
        if (self.state,to_state) in valid_transitions:
            self.state = to_state
        else:
            log.error('invalid transition')
            log.info(f"{self.state} -> error")
            self.state = 'error'
            raise ParserError('invalid transition')

    # state-machine output

    def push_paragraph(self):
        self.paragraph_action(self.paragraph)
        self.paragraph = self.paragraph.new_paragraph()

    # state-machine logic

    def dispatch(self, ms: MachineState, attrs: Attrs={}):
        if   ms == ('start','header','starttag'): 
            self.transition('metadata')

        elif ms == ('metadata','Author','DATA'):
            self.transition('author')

        elif ms == ('metadata','Date','DATA'):
            self.transition('date')

        elif ms == ('metadata','header','endtag'):
            self.transition('article')

        elif ms == ('author','*','DATA'):
            self.paragraph.author = ms.tagOrData
            self.transition('metadata')

        elif ms == ('date','*','DATA'):
            self.paragraph.date = parse_date(ms.tagOrData)
            self.transition('metadata')

        elif ms == ('article','h2','starttag'):
            self.push_paragraph()
            self.transition('subtitle')

        elif ms == ('article','*','DATA'):
            self.paragraph.text += ms.tagOrData

        elif ms == ('subtitle','*','DATA'):
            self.paragraph.paragraph_title += ms.tagOrData

        elif ms == ('subtitle','h2','endtag'):
            self.transition('article')

    # Events from base class.  These are all routed through dispatch()
    
    def handle_starttag(self, tag: str, attrs: Attrs):
        self.dispatch(MachineState(self.state,tag,'starttag'), attrs=attrs)

    def handle_endtag(self, tag: str):
        self.dispatch(MachineState(self.state,tag,'endtag'))

    def handle_data(self, data: str):
        self.dispatch(MachineState(self.state,data,'DATA'))

if __name__ == '__main__':
    filename = "./site/2020/04/18/deep-learning-for-medical-imaging-2/index.html"
    b = BlogParser()
    b.parse_file(filename)
