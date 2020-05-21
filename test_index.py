# test_index.py

from es_config import ES_CONFIG, JsonObject, my_analysis
from make_index import make_index

from elasticsearch import Elasticsearch # type: ignore
from elasticsearch.helpers import bulk  # type: ignore

from typing import List
from pprint import pprint

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


if __name__ == '__main__':
    make_index(TestIndex())
    TestIndex.add_docs_to_test()
