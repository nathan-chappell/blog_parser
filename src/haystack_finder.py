# haystack_finder.py

#import sys
#sys.path = ['C:\\Users\\nchappell\\programming\\transformers\\src'] + sys.path

from es_config import ES_CONFIG
from util import get_log

from haystack.database.elasticsearch import ElasticsearchDocumentStore # type: ignore
from haystack.database.base import Document # type: ignore
from haystack.retriever.elasticsearch import ElasticsearchRetriever # type: ignore
from haystack.retriever.base import BaseRetriever # type: ignore
from haystack.reader.farm import FARMReader # type: ignore
from haystack.reader.transformers import TransformersReader # type: ignore
from haystack import Finder # type: ignore


import multiprocessing
import pdb

model_keys = {
    'distilbert': {
        'model': 'distilbert-base-cased-distilled-squad',
        'tokenizer': 'distilbert-base-cased'
    },
    'distilbert-squad2': {
        'model': 'twmkn9/distilbert-base-uncased-squad2',
        'tokenizer': 'distilbert-base-cased'
    },
    'xlm-roberta': {
        'model': 'xlm-roberta-base',
        'tokenizer': 'xlm-mlm-en-2048'
    },
}

#
# Retriever that only has one document.  Used for testing question/ context
# against the server
#
class SingleRetriever(BaseRetriever):
    # the only document
    document: Document

    def __init__(self, context: str):
        super().__init__()
        self.document = Document(id="the only document",text=context)

    def retrieve(self, *args,**kwargs):
        return [self.document]

def get_finder(
        config: ES_CONFIG, 
        model_key = 'distilbert',
    ) -> Finder:

    documentStore = ElasticsearchDocumentStore(
            host = config.hostname,
            index = config.index,
            create_index = False,
            external_source_id_field = config.external_source_id_field,
    )

    retriever = ElasticsearchRetriever(documentStore)
    #reader = FARMReader(
            #model_name_or_path = 'distilbert-base-uncased-distilled-squad'
    #)
    #pdb.set_trace()
    reader = TransformersReader(
            #model = model,
            #tokenizer = tokenizer,
            # use_gpu = -1, # don't have nvida graphics card...
            **model_keys[model_key],
            use_gpu = 0, # ai-machine-2
    )
    finder = Finder(
            reader = reader,
            retriever = retriever
    )
    return finder

def query_loop():
    #multiprocessing.freeze_support()
    finder = get_finder(ES_CONFIG())
    from pprint import pprint
    from util import bannerfy
    query = ''
    banner = bannerfy('Answers')
    while query != 'exit':
        query = input("enter query:\n>>> ")
        answers = finder.get_answers(query, top_k_reader=3)
        print(banner)
        #pdb.set_trace()
        pprint(answers,indent=2)

def test_model_keys():
    config = ES_CONFIG()
    for key in model_keys.keys():
        print(f'getting finder for: {key}')
        get_finder(config,key)

if __name__ == '__main__':
    import os
    if os.environ.get('TEST_MT','true').lower() != 'true':
        query_loop()
    else:
        test_model_keys()

