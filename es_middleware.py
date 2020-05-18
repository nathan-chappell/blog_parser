# es_middleware.py

from util import get_log
from paragraph import Paragraph, Paragraphs

from hashlib import md5
from elasticsearch import Elasticsearch # type: ignore
from typing import Dict, Union
from pprint import pformat

log = get_log(__file__,stderr=True,mode='w')

def get_id(paragraph: Paragraph) -> str:
    id_str = paragraph.filename + paragraph.paragraph_title
    return md5(bytes(id_str,'utf-8')).hexdigest()

class ES_CONFIG:
    hostname: str = 'localhost'
    port: int = 9200
    index: str = 'site'

class ESMiddleware:
    es: Elasticsearch

    def __init__(self):
        self.es = Elasticsearch([{'hostname':ES_CONFIG.hostname,'port':ES_CONFIG.port}])

    def __call__(self, paragraphs: Paragraphs) -> Paragraphs:
        for paragraph in paragraphs:
            self.index_paragraph(paragraph)
        return paragraphs

    def index_paragraph(self, paragraph: Paragraph):
        msg = f'{paragraph.date} - {paragraph.paragraph_title}'
        id_ = get_id(paragraph)
        log.info(f'indexing {id_}: {msg}')
        result = self.es.index(
                index=ES_CONFIG.index,
                id=id_,
                body=repr(paragraph),
                )
        log.info(pformat(result))

