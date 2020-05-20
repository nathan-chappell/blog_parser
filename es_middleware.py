# es_middleware.py

from util import get_log
from paragraph import Paragraph, Paragraphs
from es_config import ES_CONFIG

from hashlib import md5
from elasticsearch import Elasticsearch # type: ignore
from typing import Dict, Union
from pprint import pformat
import json

log = get_log(__file__,stderr=True,mode='w')

def get_id(paragraph: Paragraph) -> str:
    id_str = paragraph.filename + paragraph.paragraph_title
    return md5(bytes(id_str,'utf-8')).hexdigest()

class ESMiddleware:
    es: Elasticsearch

    def __init__(self, config: ES_CONFIG = ES_CONFIG()):
        self.es = Elasticsearch(config.hosts)
        self.config = config

    def __call__(self, paragraphs: Paragraphs) -> Paragraphs:
        for paragraph in paragraphs:
            self.index_paragraph(paragraph)
        return paragraphs

    def index_paragraph(self, paragraph: Paragraph):
        flat: Dict[str,str] = paragraph.flatten()
        msg = f'{paragraph.date} - {flat["name"]}'
        id_ = get_id(paragraph)
        log.info(f'indexing {id_}: {msg}')
        result = self.es.index(
                index=self.config.index,
                id=id_,
                body=json.dumps(flat),
                )
        log.info(pformat(result))

