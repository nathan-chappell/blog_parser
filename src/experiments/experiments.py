# experiments.py

from experiments_base import ExperimentBase, Sample, Result, add_parent_dir_to_path
add_parent_dir_to_path()

from make_index import BlogIndexConfig
from haystack_server import make_finder

# TODO
#
# need to pass keyword arguments through make_finder to the finder instance...
# or maybe just add a "set_finder" function to haystack_server.py... probably
# easier

class TopKRetrieverExperiment(ExperimentBase):
    """Vary the parameter 'top_k_retriever' in the finder.
       I expect that lower top_k_retriever will have better results because
       there will be less chance for the finder to get confused by higher
       confidence in less relevant contexts"""
    
    top_k_retriever: int
    finder: Finder

    def __init__(self,top_k_retriever):
        super().__init__()
        self.top_k_retriever = top_k_retriever

