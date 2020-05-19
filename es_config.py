# es_config.py

class ES_CONFIG:
    hostname: str = 'localhost'
    port: int = 9200
    index: str = 'site'
    external_source_id_field: str = 'filename'
