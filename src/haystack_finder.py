# haystack_finder.py

#import sys
#sys.path = ['C:\\Users\\nchappell\\programming\\transformers\\src'] + sys.path

from es_config import ES_CONFIG
from util import get_log

from haystack.database.elasticsearch import ElasticsearchDocumentStore # type: ignore
from haystack.retriever.elasticsearch import ElasticsearchRetriever # type: ignore
from haystack.reader.farm import FARMReader # type: ignore
from haystack.reader.transformers import TransformersReader # type: ignore
from haystack import Finder # type: ignore

import multiprocessing
import pdb


model_tokenizers = {
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

def get_finder(
        config: ES_CONFIG, 
        model_tokenizer = 'distilbert',
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
            **model_tokenizers[model_tokenizer],
            use_gpu = 0, # ai-machine-2
    )
    finder = Finder(
            reader = reader,
            retriever = retriever
    )
    return finder

if __name__ == '__main__':
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

