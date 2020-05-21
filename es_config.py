# es_config.py

from util import get_log, bannerfy, input_command, input_prompt

from elasticsearch import Elasticsearch  # type: ignore
from typing import Dict, Any, Union, List
import re
from pprint import pprint, pformat
from logging import DEBUG

log = get_log(__file__,stderr=True)
log.setLevel(DEBUG)

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
        config = {}
        for k in ['settings','mappings']:
            if hasattr(self,k): config[k] = getattr(self,k)
        return config

