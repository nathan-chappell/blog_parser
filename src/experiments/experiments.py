# experiments.py

from experiments_base import ExperimentBase, Sample, Result, add_parent_dir_to_path
add_parent_dir_to_path()

from make_index import BlogIndexConfig, ES_CONFIG, get_all_configs
from haystack_finder import get_finder, model_tokenizers

from itertools import product

# TODO
#
# need to pass keyword arguments through get_finder to the finder instance...
# or maybe just add a "set_finder" function to haystack_server.py... probably
# easier

class TopKRetrieverExperiment(ExperimentBase):
    """Vary the parameter 'top_k_retriever' in the finder.
       I expect that lower top_k_retriever will have better results because
       there will be less chance for the finder to get confused by higher
       confidence in less relevant contexts"""
    
    top_k_retriever: int
    finder: Finder

    def __init__(self, es_config: ES_CONFIG, top_k_retriever: int):
        super().__init__(f'top_k_retriever-{top_k_retriever}-{es_config.index}')
        self.top_k_retriever = top_k_retriever
        self.finder = get_finder(es_config)

    def handle_sample(self, sample: Sample) -> Result:
        response = self.finder.get_answers(
            sample.question,
            top_k_retriever = self.top_k_retriever,
            top_k_reader = 3
        )
        result = Result.from_sample(sample)
        for prediction in response['answers']:
            result.add_prediction(prediction)
        return result

def run_all():
    top_k_retrievers = [1,2,4]
    for top_k_retriever, config in product
        
