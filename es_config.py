# es_config.py

from util import get_log, bannerfy, input_command, input_prompt

from elasticsearch import Elasticsearch  # type: ignore
from typing import Dict, Any, Union, List
import re
from pprint import pprint

log = get_log(__file__)

# Cheap, hacky JSON type.  For more details visit:
#
# https://github.com/python/mypy/issues/731
#
JsonObject = Dict[str, Union[bool, int, str, object]]

# some custom analyzers

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

    @property
    def index_config(self):
        """Configuration for Index Creation"""
        config = {}
        for k in ['settings','mappings']:
            if hasattr(self,k): config[k] = getattr(self,k)
        return config

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

    @staticmethod
    def add_docs_to_test() -> None:
        from elasticsearch.helpers import bulk  # type: ignore
        config = TestIndex()
        es = Elasticsearch(hosts=config.hosts)
        docs: List[JsonObject] = [
            {'text': "this is the first test doc", 'key': "key1"},
            {'text': "this is the second test doc", 'key': "key2"},
            {'text': "my dog likes to eat docs", 'key': "key"},
            {'text': "my cat likes to meow, docs are cool", 'key': "key"},
        ]
        for i, doc in enumerate(docs):
            doc['_id'] = i
        for doc in docs:
            doc['_index'] = config.index
        r = bulk(es, docs)
        pprint(r)


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
        safe_commands = ['change name', 'quit']
        dangerous_commands = ['replace existing']
        command = input_command(safe_commands, dangerous_commands)
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
    pprint(config.index_config, indent=2)
    try:
        r = es.indices.create(index=config.index, body=config.index_config)
        pprint(r, indent=2)
        log.info(r)
    except Exception as e:
        log.error(e)
        raise e


if __name__ == '__main__':
    make_index(TestIndex())
    TestIndex.add_docs_to_test()
