# main.py

from blog_parser import BlogParser, log
from paragraph import Paragraph, Paragraphs, ParagraphsAction
from paragraph_stats import ParagraphStatsCollector
from util import bannerfy, get_log

from pprint import pprint, pformat
from glob import glob
from typing import List
import re

log = get_log(__file__, stderr=True, mode='w')

#
# basic paragraph actions
#

def pa_log(paragraphs: Paragraphs) -> Paragraphs:
    log.info("\n".join(map(str,paragraphs)))
    return paragraphs

def pa_sanitize_ws(paragraphs: Paragraphs) -> Paragraphs:
    def sanitize_ws(paragraph: Paragraph):
        paragraph.text = re.sub("\s+",' ',paragraph.text).strip()
    for paragraph in paragraphs: sanitize_ws(paragraph)
    return paragraphs

if __name__ == '__main__':
    filenames = glob('./site/20*/**/*index.html',recursive=True)
    paragraphStatsCollector = ParagraphStatsCollector()
    middlewares: List[ParagraphsAction] = [
        pa_sanitize_ws,
        pa_log,
        paragraphStatsCollector,
    ]
    blogParser = BlogParser(middlewares)
    filenames = ['./site/2017/04/11/custom-intellisense-with-monaco-editor/index.html']
    log.info(pformat(filenames,indent=2))
    for filename in filenames:
        blogParser.parse_file(filename)
    formattedStats = paragraphStatsCollector.formatted()
    log.info(bannerfy(f"Gathered Statistics:\n{formattedStats}"))

