# es_config.py

from util import get_log, bannerfy, input_command, input_prompt

from elasticsearch import Elasticsearch  # type: ignore

from typing import Dict, Any, Union, List
import re
from pprint import pprint, pformat
from logging import DEBUG
from hashlib import md5
from json import dumps

log = get_log(__file__,stderr=True)
log.setLevel(DEBUG)

# Cheap, hacky JSON type.  For more details visit:
#
# https://github.com/python/mypy/issues/731
#
JsonObject = Dict[str, Union[bool, int, str, object]]

# some custom analyzers

def get_my_analyzer(stemmer=False,stopwords=False) -> JsonObject:
    filters = ['asciifolding','lowercase']
    if stemmer: filters.append('my_stopword_filter')
    if stopwords: filters.append('stemmer')

    return {
        'type': 'custom',
        'tokenizer': 'standard',
        'filter': filters
    }

def get_my_analysis(stemmer=False,stopwords=False):
    my_stopword_filter: JsonObject = {
        'type': 'stop',
        'ignore_case': True,
        'stopwords_path': './stopwords',
    }

    my_analysis: JsonObject = {
        'analyzer': {'my_analyzer': get_my_analyzer(stemmer,stopwords)},
        'filter': {'my_stopword_filter': my_stopword_filter},
    }
    #if stopwords:
        #my_analysis.update({'filter': {'my_stopword_filter': my_stopword_filter}})

    return my_analysis

class ES_CONFIG:
    hostname: str = 'localhost'
    port: int = 9200
    external_source_id_field: str = 'filename'
    index: str = 'site'

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

    @property
    def hexdigest(self) -> str:
        # sort_keys=True is crucial here:
        return md5(bytes(dumps(self.index_config, sort_keys=True),'utf-8')).hexdigest()
    
    @property
    def description(self) -> List[str]:
        cls_name = self.__class__.__name__
        loc = f"{self.hostname}:{self.port}/{self.index}"
        return [cls_name, loc, self.hexdigest]
