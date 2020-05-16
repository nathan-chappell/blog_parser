# blog_parser.py

from util import get_log, bannerfy
from paragraph import Paragraph
from paragraph_stats import ParagraphStatsCollector
from machine_html_parser import State, Attrs 
from machine_html_parser import TransitionData, MachineHTMLParser

from typing import List, Iterable, Tuple, Optional, FrozenSet
from typing import Callable
from datetime import datetime, timedelta
from pprint import pprint, pformat
from functools import reduce
import json
import re
import logging

log = get_log(__file__,stderr=True)
#log.setLevel(logging.DEBUG)

#
# a ParagraphAction takes a paragraph, performs some action, then returns
# the (potentially modified) paragraph for further processing.  The
# functions are called with reduce (similar to redux)
#
ParagraphAction = Callable[[Paragraph],Paragraph]

#
# basic paragraph actions
#

def pa_log(paragraph: Paragraph) -> Paragraph:
    log.info(str(paragraph))
    return paragraph

def pa_sanitize_ws(paragraph: Paragraph) -> Paragraph:
    paragraph.text = re.sub("\s+",' ',paragraph.text).strip()
    return paragraph
    # state-machine logic
    # TODO make this class a base class, move logic to subclass
    # (or dependency)


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
    ('article','done'),
])

class BlogParser(MachineHTMLParser):
    paragraph_actions: List[ParagraphAction]
    paragraph: Paragraph

    def parse_file(self, filename: str):
        self.reset()
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

    def __init__(self, paragraph_actions: List[ParagraphAction] = []):
        super().__init__()
        self.paragraph_actions = paragraph_actions
        self.paragraph = Paragraph()

    # state-machine output

    def push_paragraph(self):
        reduce(lambda x,f: f(x), self.paragraph_actions, self.paragraph)
        self.paragraph = self.paragraph.new_paragraph()

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

        elif ms == ('article','h2','starttag'):
            self.push_paragraph()
            self.transition('subtitle')

        elif ms == ('article','*','DATA'):
            self.paragraph.text += ms.tagOrData

        elif ms == ('article','article','endtag'):
            self.push_paragraph()
            self.transition('done')

        elif ms == ('subtitle','*','DATA'):
            self.paragraph.paragraph_title += ms.tagOrData

        elif ms == ('subtitle','h2','endtag'):
            self.transition('article')

if __name__ == '__main__':
    from glob import glob
    from functools import partial
    filenames = glob('./site/20*/**/*index.html',recursive=True)
    pprint(filenames,indent=2)
    paragraphStatsCollector = ParagraphStatsCollector()
    middlewares: List[ParagraphAction] = [
        pa_sanitize_ws,
        pa_log,
        paragraphStatsCollector,
    ]
    blogParser = BlogParser(middlewares)
    filenames = ['./site/2017/04/11/custom-intellisense-with-monaco-editor/index.html']
    for filename in filenames:
        blogParser.parse_file(filename)
    formattedStats = paragraphStatsCollector.formatted()
    log.info(bannerfy(f"Gathered Statistics:\n{formattedStats}"))

