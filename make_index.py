# make_index.py

from blog_parser import BlogParser
from paragraph_stats import ParagraphStatsCollector
from util import bannerfy, get_log
from middlewares import Middlewares, pa_log, pa_sanitize_ws, pa_chunk_long
from middlewares import pa_remove_empty, pa_cat_short, pa_remove_ptag
from es_middleware import ESMiddleware
from es_config import ES_CONFIG, my_analyzer, my_analysis

from pprint import pformat
from glob import glob
from logging import DEBUG

log = get_log(__file__, stderr=True, mode='w')
log.setLevel(DEBUG)

class BlogIndexConfig(ES_CONFIG):
    index: str = 'site'

    mappings: JsonObject = {
        'properties': {
            'text': {
                'type': 'text',
                'analyzer': 'my_analyzer'
            },
            'key': {'type': 'keyword'}
        }
    }

    index_settings: JsonObject = {
        'index': {
            'number_of_shards': 1,
        },
        'analysis': my_analysis,
    }


def parse_blogs(site_dir: str ='./site', config: ES_CONFIG = ES_CONFIG):
    filenames = glob(site_dir + '/20*/**/*index.html',recursive=True)
    paragraphStatsCollector = ParagraphStatsCollector()
    middlewares: Middlewares = [
        pa_sanitize_ws,
        pa_chunk_long,
        pa_remove_empty,
        pa_cat_short,
        pa_remove_ptag,
        paragraphStatsCollector,
        pa_log,
        ESMiddleware(config),
    ]
    blogParser = BlogParser(middlewares)
    #filenames = ['./site/2017/04/11/custom-intellisense-with-monaco-editor/index.html']
    log.info(pformat(filenames,indent=2))
    for filename in filenames:
        blogParser.parse_file(filename)
    formattedStats = paragraphStatsCollector.formatted()
    log.info(bannerfy(f"Gathered Statistics:\n{formattedStats}"))

#
# paragraph actions
#
if __name__ == '__main__':
    parse_blogs()
