# make_index.py

from blog_parser import BlogParser
from paragraph import Paragraph
from paragraph_stats import ParagraphStatsCollector
from util import bannerfy, get_log, input_command, get_new_name
from middlewares import Middlewares, pa_log, pa_sanitize_ws, pa_chunk_long
from middlewares import pa_remove_empty, pa_cat_short, pa_remove_ptag
from es_middleware import ESMiddleware
from es_config import ES_CONFIG, my_analyzer, my_analysis, JsonObject

from elasticsearch import Elasticsearch # type: ignore

from pprint import pprint, pformat
from glob import glob
from logging import DEBUG
from typing import Dict
from itertools import chain

log = get_log(__file__, stderr=True, mode='w')
log.setLevel(DEBUG)

class BlogIndexConfig(ES_CONFIG):
    index: str = 'site'

    # the only reason this is a property is that it is a bit convoluted to
    # create
    @property
    def mappings(self):
        default_prop: Dict[str, str] = {
            'type': 'text', 'analyzer': 'my_analyzer'
        }
        properties: Iterable[str] = list(chain(Paragraph.attrs, ['name','text']))

        mappings: JsonObject = {
            'properties': {k: default_prop.copy() for k in properties}
        }
        mappings['properties']['date']['type'] = 'date'
        del mappings['properties']['date']['analyzer']

        return mappings

    settings: JsonObject = {
        'index': {
            'number_of_shards': 1,
        },
        'analysis': my_analysis,
    }


def parse_blogs(site_dir: str, config: ES_CONFIG) -> None:
    filenames = glob(site_dir + '/20*/**/*index.html', recursive=True)
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
    log.info(pformat(filenames, indent=2))
    for filename in filenames:
        blogParser.parse_file(filename)
    formattedStats = paragraphStatsCollector.formatted()
    log.info(bannerfy(f"Gathered Statistics:\n{formattedStats}"))

class MakeIndexCancelled(Exception): pass

def make_index(config: ES_CONFIG):
    es = Elasticsearch(config.hosts)

    if es.indices.exists(config.index):
        print(bannerfy(f'index: {config.index} already exists'))
        c_replace = 'delete existing'
        c_continue = 'cancel'
        c_new_name = 'enter new name'
        c_new = 'make new'
        safe_commands = [c_continue, c_new_name]
        dangerous_commands = [c_replace]
        command = input_command(safe_commands, dangerous_commands)
    else:
        command = c_new

    if command == c_new:
        pass
    elif command == c_new_name:
        config.index = get_new_name(config.index)
    elif command == c_replace:
        es.indices.delete(config.index)
    elif command == c_continue:
        raise MakeIndexCancelled('user cancelled the operation')
    else:
        raise RuntimeError('not reachable')

    msg = f'making index: {config.index}: {config.index_config}'
    log.info(msg)
    try:
        r = es.indices.create(index=config.index, body=config.index_config)
        log.info(r)
    except Exception as e:
        log.error(e)
        raise e

def make_default_index() -> ES_CONFIG:
    config = BlogIndexConfig()
    try:
        make_index(config)
        parse_blogs('./site',config)
    except MakeIndexCancelled:
        pass
    return config

if __name__ == '__main__':
    make_default_index()
