# experiments.py

from experiments_base import ExperimentBase, Sample, Result, add_parent_dir_to_path
from experiments_base import is_test_run
add_parent_dir_to_path()
from util import get_log # type: ignore

from make_index import BlogIndexConfig, ES_CONFIG, get_all_configs # type: ignore
from haystack_finder import get_finder, model_keys # type: ignore

from haystack.finder import Finder # type: ignore

from itertools import product
from logging import INFO,DEBUG
from pprint import pformat

log = get_log(__file__)
log.setLevel(DEBUG)


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
    config: ES_CONFIG

    def __init__(self, config: ES_CONFIG, top_k_retriever: int):
        super().__init__(f'top_k_retriever-{top_k_retriever}-{config.index}')
        self.top_k_retriever = top_k_retriever
        self.finder = get_finder(config)
        self.config = config

    def handle_sample(self, sample: Sample) -> Result:
        response = self.finder.get_answers(
            sample.question,
            top_k_retriever = self.top_k_retriever,
            top_k_reader = 3
        )
        result = Result.from_sample(sample)
        result.experiment_name = self.name
        for prediction in response['answers']:
            additional_metadata = {
                'document_id': prediction.get('document_id','?'),
                'index': self.config.index,
            }
            result.add_prediction(prediction,additional_metadata=additional_metadata)
        return result

def run_all():
    import os
    top_k_retrievers = [1,2,4]

    # add model_keys
    for top_k_retriever, config in product(top_k_retrievers, get_all_configs()): 
        experiment = TopKRetrieverExperiment(config, top_k_retriever)
        experiment.test_run = is_test_run()
        experiment.run_experiment()

if __name__ == '__main__':
    run_all()
