# main.py

from blog_parser import BlogParser
from paragraph_stats import ParagraphStatsCollector
from util import bannerfy, get_log
from middlewares import Middlewares, pa_log, pa_sanitize_ws, pa_chunk_long
from middlewares import pa_remove_empty, pa_cat_short

from pprint import pformat
from glob import glob
from logging import DEBUG

log = get_log(__file__, stderr=True, mode='w')
log.setLevel(DEBUG)

#
# paragraph actions
#
if __name__ == '__main__':
    filenames = glob('./site/20*/**/*index.html',recursive=True)
    paragraphStatsCollector = ParagraphStatsCollector()
    middlewares: Middlewares = [
        pa_sanitize_ws,
        pa_log,
        pa_chunk_long,
        pa_remove_empty,
        pa_cat_short,
        paragraphStatsCollector,
    ]
    blogParser = BlogParser(middlewares)
    #filenames = ['./site/2017/04/11/custom-intellisense-with-monaco-editor/index.html']
    log.info(pformat(filenames,indent=2))
    for filename in filenames:
        blogParser.parse_file(filename)
    formattedStats = paragraphStatsCollector.formatted()
    log.info(bannerfy(f"Gathered Statistics:\n{formattedStats}"))

