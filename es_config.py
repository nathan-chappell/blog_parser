# es_config.py

from util import get_log, bannerfy

from elasticsearch import Elasticsearch  # type: ignore
from typing import Dict, Any, Union, List
import re

log = get_log(__file__)
input_prompt = "$ "

# Cheap, hacky JSON type.  For more details visit:
#
# https://github.com/python/mypy/issues/731
#
JsonObject = Dict[str, Union[bool, int, str, object]]


class ES_CONFIG:
    hostname: str = 'localhost'
    port: int = 9200
    index: str = 'site'
    external_source_id_field: str = 'filename'

    @property
    def hosts(self):
        """Get list of hosts for use with Elasticsearch constructor"""
        return [{'host': self.hostname, 'port': self.port}]

    @property
    def index_config(self):
        """Configuration for Index Creation"""
        return None


my_analyzer: JsonObject = {
    'type': 'custom',
    'tokenizer': 'standard',
    'filter': [
            'asciifolding',
            'lowercase',
            'my_stopword_filter',
            'stemmer',
    ]
}
my_stopword_filter: JsonObject = {
    'type': 'stop',
    'ignore_case': True,
    'stopwords_path': './stopwords/english_removed_question_words',
}

my_analysis: JsonObject = {
    'analyzer': {'my_analyzer': my_analyzer},
    'filter': {'my_stopword_filter': my_stopword_filter}
}


class TestIndex(ES_CONFIG):
    index: str = 'test'

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

    @property
    def index_config(self):
        """Configuration for Index Creation"""
        return {
            'settings': self.index_settings,
            'mappings': self.mappings
        }

def confirm_command(msg: str = "") -> bool:
    msg_ = "?" if not msg else " you wish to " + msg + "?"
    message = "are you sure" + msg_
    print(message)
    while True:
        confirm = input("[y]es or [n]o: ").lower().strip()
        if confirm == "": continue
        elif re.match(confirm, 'yes'): return True
        elif re.match(confirm, 'no'): return False
        else: print('please enter y/ye/yes, or n/no')


def get_index_command() -> str:
    commands: List[str] = ['change name', 'replace existing', 'quit']
    commands_prompt: List[str] = list(map(lambda s: f'[{s[0]}]{s[1:]}', commands))
    while True:
        print(f"enter command: {commands_prompt}")
        cmd = input(input_prompt).lower().strip()
        if cmd == "": continue
        def matcher(s): return re.match(cmd, s) is not None
        candidates = list(filter(matcher, commands))
        if candidates:
            cmd = candidates[0]
            confirm = True
            if cmd == 'replace existing':
                confirm = confirm_command('delete existing index')
            if confirm:
                return candidates[0]
        else: 
            print(f'Did not recognize: {cmd}')


def get_new_name() -> str:
    name = ""
    while name == "" or not name.isalnum():
        print('please enter an alpha-numeric index name:')
        name = input(input_prompt)
    return name


def make_index(config: ES_CONFIG):
    es = Elasticsearch(config.hosts)

    if es.indices.exists(config.index):
        print(bannerfy(f'index: {config.index} already exists'))
        command = get_index_command()
    else:
        command = 'make new'

    if command == 'make new':
        pass
    elif command == 'change name':
        config.index = get_new_name()
    elif command == 'replace existing':
        es.indices.delete(config.index)
    elif command == 'quit':
        raise Exception('quitting')
    else:
        raise RuntimeError('not reachable')

    msg = f'making index: {config.index}: {config.index_config}'
    log.info(msg)
    print(f'make_index: {config.index}')
    pprint(config.index_config,indent=2)
    try:
        r = es.indices.create(index=config.index, body=config.index_config)
        pprint(r, indent=2)
        log.info(r)
    except Exception as e:
        log.error(e)
        raise e

def add_docs_to_test() -> None:
    from elasticsearch.helpers import bulk # type: ignore
    config = TestIndex()
    es = Elasticsearch(hosts=config.hosts)
    docs = [
        {'text': "this is the first test doc", 'key': "key1" },
        {'text': "this is the second test doc", 'key': "key2" },
        {'text': "my dog likes to eat docs", 'key': "key" },
        {'text': "my cat likes to meow, docs are cool", 'key': "key" },
    ]
    for i,doc in enumerate(docs): doc['_id'] = i
    for doc in docs: doc['_index'] = config.index
    r = bulk(es, docs)
    pprint(r)

if __name__ == '__main__':
    from pprint import pprint
    import json
    make_index(TestIndex())
    add_docs_to_test()
