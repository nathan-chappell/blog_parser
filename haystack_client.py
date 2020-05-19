# haystack_client.py

from es_config import ES_CONFIG

from haystack.database.elasticsearch import ElasticsearchDocumentStore
from haystack.retriever.elasticsearch import ElasticsearchRetriever

documentStore = ElasticsearchDocumentStore(
        host = ES_CONFIG.hostname,
        index = ES_CONFIG.index,
        create_index = False,
        external_source_id_field = ES_CONFIG.external_source_id_field,
)

retriever = ElasticsearchRetriever(documentStore)

