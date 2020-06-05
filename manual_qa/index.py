# synonyms.py

# given a list of paragraphs (lists of words), come up with a reasonable base
# for a synonmy file for ElasticSearch.  The files will probably need to be
# manually reviewed

from typing import List, Set, Dict, Tuple, Any, Callable, DefaultDict, cast
import re
import math
import sys
from collections import defaultdict
from logging import getLogger, StreamHandler, Formatter, INFO

from util import is_test, get_logger, smooth_split, Protocol
from score_functions import ScoreFunction, f1_weighted_score, Score
from analyzer import Analyzer, StandardAnalyzer, Paragraph
from paragraph_info import ParagraphInfo

log = get_logger(__file__)

InfoIndex = int

class Index:
    """Take a list of paragraphs, make a reverse index and vocab set"""
    _reverse_index: DefaultDict[str, List[InfoIndex]]
    _paragraph_info: Dict[InfoIndex, ParagraphInfo]
    _idfs: Dict[str,float]
    _idfs_valid: bool
    _analyzer: Analyzer
    _score_function: ScoreFunction
    
    def __init__(self, analyzer: Analyzer, score_function: ScoreFunction):
        self._analyzer = analyzer
        self._reverse_index = defaultdict(list)
        self._paragraph_info = {}
        self._idfs = {}
        self._idfs_valid = True
        self._score_function = score_function

    @property
    def paragraphs(self) -> List[Paragraph]:
        return [info.paragraph for info in self._paragraph_info.values()]

    @property
    def vocab(self) -> Set[str]:
        return set(self._reverse_index.keys())

    @property
    def idfs(self) -> Dict[str,float]:
        if not self._idfs_valid:
            log.info('IDFs not valid, recalculating...')
            self._calc_idfs()
        return self._idfs

    def index_paragraph(self, paragraph: Paragraph, metadata: Dict[str,Any] = {}):
        """Adds paragraph to list, words to vocab/ reverse index"""
        info_index = self._get_index(paragraph)
        if info_index in self._paragraph_info:
            return
        info = ParagraphInfo(paragraph, self._analyzer, metadata)
        self._paragraph_info[info_index] = info
        for word in info.bag_of_words:
            self._reverse_index[word].append(info_index)
        self._idfs_valid = False

    def idf(self, word: str) -> float:
        """IDF as it is calculated for BM25"""
        n = len(self.paragraphs)
        df = len(self._reverse_index[word])
        return math.log((n+1.)/(df+.5))

    def query(self, query_: str) -> List[Tuple[ParagraphInfo,Score]]:
        result: List[Tuple[ParagraphInfo,Score]] = []
        candidate_indices: Set[InfoIndex] = set()
        query_info = ParagraphInfo(query_, self._analyzer)
        log.debug(f"ParagraphInfo(query):\n{query_info}")
        query_bag = query_info.bag_of_words
        for word in query_bag:
            candidate_indices.update(self._reverse_index.get(word,[]))
        for info_index in candidate_indices:
            paragraph_info = self._paragraph_info[info_index]
            score = self._score_function(self, query_info, paragraph_info)
            result.append((paragraph_info, score))
        result = sorted(result,key=lambda t: t[1], reverse=True)
        return result

    def _calc_idfs(self):
        self._idfs = dict([(word, self.idf(word)) for word in self.vocab])
        self._idfs_valid = True

    def _get_index(self, paragraph: Paragraph) -> InfoIndex:
        return paragraph.__hash__()

    def print_idfs(self,filename=''):
        if filename: file = open(filename,'w')
        else: file = None
        idfs = list(self.idfs.items())
        #for paragraph in self.paragraphs:
            #print('*'*40)
            #print(paragraph)
        #print('*'*40)
        idfs = sorted(idfs, key=lambda t:t[1])
        i = 0
        cur = []
        for word,score in idfs:
            cur.append(f'---- {word:15} {score:5.3f}')
            i+=1
            if i % 4 == 0:
                line = ' | '.join(cur)
                if file: print(line,file=file)
                else: print(line)
                cur = []

class TrainableIndex(Index):
    _hidden_doc_counts: DefaultDict[str,int]
    _hidden_docs: int

    def __init__(self, analyzer: Analyzer, score_function: ScoreFunction):
        super().__init__(analyzer, score_function)
        self._hidden_doc_counts = defaultdict(int)
        self._hidden_docs = 0

    def train(self, paragraph: Paragraph):
        vocab = self.vocab
        if not vocab:
            raise Warning("TrainableIndex can't train with an empty"
                          "vocabulary.  Index some paragraphs first!")
        tokens = set(self._analyzer(paragraph))
        tokens = vocab.intersection(tokens)
        # don't bother training with no useful info
        if not tokens:
            return
        self._hidden_docs += 1
        for token in tokens:
            self._hidden_doc_counts[token] += 1
        self._idfs_valid = False

    def idf(self, word: str) -> float:
        """Hidden counts are used to adjust idf scores"""
        n = len(self.paragraphs) + self._hidden_docs
        df = len(self._reverse_index[word]) + self._hidden_doc_counts[word]
        return math.log((n+1.)/(df+.5))


class StandardIndex(TrainableIndex):
    def __init__(self):
        scorer = cast(ScoreFunction, f1_weighted_score)
        super().__init__(StandardAnalyzer(), scorer)

def test_with_parser() -> Index:
    from qa_parser import QAParser
    parser = QAParser()
    qa_pairs = parser.parse_file('chatbot_qa.md')
    index = StandardIndex()
    for qa in qa_pairs:
        index.index_paragraph(qa.question)
        #index.index_paragraph(qa.answer)
    return index

def transform_query(query: str) -> str:
    query = query.lower()
    query = query.replace('you','Mono')
    return query

def run_queries(index: Index):
    q = ''
    while q != 'exit':
        print('*'*60)
        q = input('enter query: ')
        q = transform_query(q)
        results = index.query(q)
        for p,s in results[:10]:
            print('paragraph:')
            print("\n".join('---- ' + l for l in smooth_split(p.paragraph, 80)))
            print(f'score: {s:6.2f}')

if __name__ == '__main__':
    index = test_with_parser()
    if not is_test():
        run_queries(index)

