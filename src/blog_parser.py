# blog_parser.py

from util import get_log, bannerfy
from paragraph import Paragraph, Paragraphs, ParagraphsAction
from machine_html_parser import State, Attrs 
from machine_html_parser import TransitionData, MachineHTMLParser

from typing import List, Iterable, Tuple, Callable, Optional
from datetime import datetime
from functools import reduce
from pathlib import Path
from logging import DEBUG

log = get_log(__file__,stderr=True)
log.setLevel(DEBUG)

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
    ('metadata','title'),
    ('title','metadata'),
    ('metadata','author_1'),
    ('author_1','author_2'),
    ('author_2','metadata'),
    ('metadata','date_1'),
    ('date_1','date_2'),
    ('date_2','metadata'),
    ('metadata','article'),
    ('article','subtitle'),
    ('subtitle','article'),
    ('article','pre'),
    ('pre','article'),
    ('article','done'),
])

class BlogParser(MachineHTMLParser):
    paragraphs_actions: List[ParagraphsAction]
    paragraph: Paragraph

    def __init__(self, paragraphs_actions: List[ParagraphsAction] = []):
        super().__init__()
        self.paragraphs_actions = paragraphs_actions
        self.paragraph = Paragraph()

    # utilities

    def parse_file(self, filename: str, rel: Optional[str] = None):
        self.reset()
        if isinstance(rel, str):
            self.paragraph.filename = Path(rel).relative_to(rel)
        else:
            self.paragraph.filename = filename
        super().parse_file(filename)

    def parse_date(self, time: str) -> str:
        time_ = time.strip()
        fmt = '%A, %b %d, %Y' # example: Monday, Jan 1, 2015
        try:
            return datetime.strptime(time_, fmt).isoformat()
        except ValueError:
            log.error(f'Invalid date format:"{time_}"') 
            log.error(f'Invalid date format @ {self.location()}')
            return ""

    # reduce middleware once paragraph is read

    def push_paragraph(self):
        reduce(lambda x,f: f(x), self.paragraphs_actions, [self.paragraph])
        self.paragraph = self.paragraph.new_paragraph()

    # state-machine logic

    def reset(self):
        super().reset()
        self.state = 'start'
        self.paragraph = Paragraph()

    def validate_transition(self, to_state: State):
        return (self.state, to_state) in valid_transitions

    def dispatch(self, ms: TransitionData, attrs: Attrs={}):
        if   ms == ('start','header','starttag'): 
            self.transition('metadata')

        elif ms == ('metadata','h1','starttag'):
            self.transition('title')

        elif ms == ('metadata','Author','DATA'):
            self.transition('author_1')

        elif ms == ('metadata','Date','DATA'):
            self.transition('date_1')

        elif ms == ('metadata','header','endtag'):
            self.transition('article')

        elif ms == ('title','*','DATA'):
            self.paragraph.article_title = ms.tagOrData

        elif ms == ('title','h1','endtag'):
            self.transition('metadata')

        elif ms == ('author_1','p','starttag'): 
            self.transition('author_2')

        elif ms == ('author_2','*','DATA'):
            self.paragraph.author = ms.tagOrData
            self.transition('metadata')

        elif ms == ('date_1','p','starttag'): 
            self.transition('date_2')

        elif ms == ('date_2','*','DATA'):
            self.paragraph.date = self.parse_date(ms.tagOrData)
            self.transition('metadata')

        elif ms == ('article','h[23]','starttag'):
            self.push_paragraph()
            self.transition('subtitle')

        elif ms == ('subtitle','h[23]','endtag'):
            self.transition('article')

        elif ms == ('article','article','endtag'):
            self.push_paragraph()
            self.transition('done')

        elif ms == ('article','*','DATA'):
            self.paragraph.text += ms.tagOrData

        # remove pre-formatted code

        elif ms == ('article','pre','starttag'):
            self.transition('pre')

        elif ms == ('pre','pre','endtag'):
            self.transition('article')

        # we keep and <p> tags for use in chunking text later
        # no longer keeping <code> tags, they weren't helpful

        elif ms == ('article','p','starttag'):
            self.paragraph.text += "<p>"

        elif ms == ('article','p','endtag'):
            self.paragraph.text += "</p>"

        elif ms == ('subtitle','*','DATA'):
            self.paragraph.paragraph_title += ms.tagOrData
