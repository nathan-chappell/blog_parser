# make_index.py

from blog_parser import BlogParser
from paragraph import Paragraph
from paragraph_stats import ParagraphStatsCollector
from util import bannerfy, get_log, input_command, get_new_name
from middlewares import Middlewares, pa_log, pa_sanitize_ws, pa_chunk_long
from middlewares import pa_remove_empty, pa_cat_short, pa_remove_ptag
from es_middleware import ESMiddleware
from es_config import ES_CONFIG, get_my_analyzer, get_my_analysis, JsonObject

from elasticsearch import Elasticsearch # type: ignore

from pprint import pprint, pformat
from glob import glob
from logging import DEBUG, WARN
from typing import Dict, Iterable, List
from itertools import chain, product

log = get_log(__file__, stderr=True, mode='w')
log.setLevel(DEBUG)

class BlogIndexConfig(ES_CONFIG):
    stemmer: bool
    stopwords: bool

    def __init__(self,stemmer=False,stopwords=False):
        super().__init__()
        self.stemmer = stemmer
        self.stopwords = stopwords
        self.index = self._make_index_name()

    def _make_index_name(self) -> str:
        desc = [
            'site',
            'stemmer' if self.stemmer else 'nostemmer',
            'stopwords' if self.stopwords else 'nostopword',
            ]
        return '_'.join(desc)

    # the only reason this is a property is that it is a bit convoluted to
    # create
    @property
    def mappings(self) -> JsonObject:
        default_prop: Dict[str, str] = {
            'type': 'text', 'analyzer': 'my_analyzer'
        }
        properties: Iterable[str] = list(chain(Paragraph.attrs, ['name','text']))

        mappings: JsonObject = {
            'properties': {k: default_prop.copy() for k in properties}
        }
        #
        # ignoring typing here because I don't have a goo JsonObject type...
        #
        mappings['properties']['date']['type'] = 'date' # type: ignore
        del mappings['properties']['date']['analyzer'] # type: ignore

        return mappings

    @property
    def settings(self) -> JsonObject: 
        return {
            'index': { 'number_of_shards': 1 },
            'analysis': get_my_analysis(self.stemmer,self.stopwords),
        }

def get_all_configs() -> List[ES_CONFIG]:
    configs: List[ES_CONFIG] = []
    for stem_opt, stopword_opt in product([True,False],[True,False]):
        configs.append(BlogIndexConfig(stem_opt, stopword_opt))
    return configs

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
    c_replace = 'delete existing'
    c_continue = 'cancel'
    c_new_name = 'enter new name'
    c_new = 'make new'
    safe_commands = [c_continue, c_new_name]
    dangerous_commands = [c_replace]

    if es.indices.exists(config.index):
        print(bannerfy(f'index: {config.index} already exists'))
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

def try_make_index(config: ES_CONFIG) -> None:
    try:
        make_index(config)
        parse_blogs('../site',config)
    except MakeIndexCancelled:
        pass

def make_default_index(stemming=False,stopwords=True) -> ES_CONFIG:
    config = BlogIndexConfig(stemming, stopwords)
    try_make_index(config)
    return config

def make_all_indices() -> None:
    for config in get_all_configs():
        try:
            make_index(config)
            parse_blogs('../site',config)
        except MakeIndexCancelled:
            pass

if __name__ == '__main__':
    # make_default_index()
    make_all_indices()
