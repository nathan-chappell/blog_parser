# synonyms.py

# given a list of paragraphs (lists of words), come up with a reasonable base
# for a synonmy file for ElasticSearch.  The files will probably need to be
# manually reviewed

from typing import List, Set, Dict, Tuple, Any, Callable
import re
import math
import sys
from pprint import pformat
from logging import getLogger, StreamHandler, Formatter, INFO
if sys.version_info > (3,7):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from util import is_test, get_logger, smooth_split

log = get_logger(__file__)

Paragraph = str
BagOfWords = Set[str]
Index = int
Score = float
#Tokenizer = Callable[Paragraph,List[str]]
#tokenizer = nltk.tokenize.NLTKTokenizer()

def harmonic_mean(h1, h2):
    assert h1*h2 != 0
    return 2 / (1/h1 + 1/h2)

def f1(l: Set[Any], r: Set[Any]):
    l_l = len(l)
    l_r = len(r)
    if l_l == 0 and l_r == 0:
        return 1
    elif l_l == 0 or l_r == 0:
        return 0
    l_i = len(l.intersection(r))
    if l_i == 0:
        return 0
    return harmonic_mean(l_i/l_l, l_i/l_r)

# Defining this as a Protocol will allow, say, the nltk tokenizers to be used
# as Tokenizers and still play nice with mypy (without having to make a bunch
# of ugly lambdas...)
class Tokenizer(Protocol):
    def tokenize(self, paragraph: Paragraph) -> List[str]: ...

class NaiveTokenizer:
    """Splits on all non-word symbols, lowercases, removes empties"""
    def __init__(self):
        super().__init__()
        
    def tokenize(self, words: str) -> List[str]:
        result: Any = None
        result = re.split('\W+', words)
        result = filter(lambda s: re.match('\w+',s), result)
        result = map(lambda s: s.lower(), result)
        return list(result)

class ParagraphInfo:
    """Keeps track of tf counts for paragraph to avoid many recomputations"""
    _tfs: Dict[str,int]
    _paragraph: Paragraph
    _metadata: Dict[str,Any]

    def __init__(self, 
                 paragraph: Paragraph,
                 tokenizer: Tokenizer,
                 metadata: Dict[str,Any] = {}
            ):
        self._paragraph = paragraph
        tfs: Dict[str,int] = {}
        words = tokenizer.tokenize(paragraph)
        for word in words:
            tfs.setdefault(word,0)
            tfs[word] += 1
        self._tfs = tfs
        self._metadata = metadata

    def count(self,word: str) -> int:
        return self._tfs.get(word,0)

    @property
    def bag_of_words(self) -> BagOfWords:
        return set(self._tfs.keys())

    @property
    def paragraph(self) -> Paragraph:
        return self._paragraph

    @property
    def metadata(self) -> Dict[str,Any]:
        return self._metadata

    def __repr__(self) -> str:
        strs = []
        strs.append('ParagraphInfo(')
        strs.append(self._paragraph)
        strs.append(pformat(self._tfs))
        strs.append(pformat(self._metadata))
        return "\n".join(strs)

ScoreFunction = Callable[['Processor',ParagraphInfo,ParagraphInfo],float]

class ScoreFunctions:

    @staticmethod
    def sum_idf_score(processor: 'Processor', l: ParagraphInfo, r: ParagraphInfo) -> float:
        common_words = l.bag_of_words.intersection(r.bag_of_words)
        return sum([processor.idf(word) for word in common_words])

    @staticmethod
    def f1_weighted_score(processor: 'Processor', l: ParagraphInfo, r: ParagraphInfo) -> float:
        score = ScoreFunctions.sum_idf_score(processor,l,r)
        f1_ = f1(l.bag_of_words, r.bag_of_words)
        if f1_ > .5: f1_ += .1
        if f1_ > .9: f1_ += 1
        return f1_*score

class Processor:
    """Take a list of paragraphs, make a reverse index and vocab set"""
    _reverse_index: Dict[str, List[Index]]
    _paragraph_info: Dict[Index, ParagraphInfo]
    _idfs: Dict[str,float]
    _idfs_valid: bool
    _tokenizer: Tokenizer
    # these instance function variables are a nightmare in general, and in
    # particular with mypy.  See:
    #
    # https://github.com/python/mypy/issues/708
    #
    #_score_function: ScoreFunction
    
    def __init__(self, 
                 tokenizer: Tokenizer = NaiveTokenizer(),
                 score_function: ScoreFunction = ScoreFunctions.f1_weighted_score
                 ):
        self._tokenizer = tokenizer
        self._reverse_index = {}
        self._paragraph_info = {}
        self._idfs = {}
        self._idfs_valid = True
        self._score_function = score_function # type: ignore

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

    def process_paragraph(self, paragraph: Paragraph, metadata: Dict[str,Any] = {}):
        """Adds paragraph to list, words to vocab/ reverse index"""
        index = self._get_index(paragraph)
        if index in self._paragraph_info:
            return
        info = ParagraphInfo(paragraph, self._tokenizer, metadata)
        self._paragraph_info[index] = info
        for word in info.bag_of_words:
            self._reverse_index.setdefault(word,[])
            self._reverse_index[word].append(index)
        self._idfs_valid = False

    def tokenize(self, paragraph: Paragraph) -> List[str]:
        return self._tokenizer.tokenize(paragraph)

    def idf(self, word: str) -> float:
        """IDF as it is calculated for BM25"""
        n = len(self.paragraphs)
        df = len(self._reverse_index[word])
        return math.log((n+1.)/(df+.5))

    def query(self, query_: str) -> List[Tuple[ParagraphInfo,Score]]:
        result: List[Tuple[ParagraphInfo,Score]] = []
        candidate_indices: Set[Index] = set()
        query_info = ParagraphInfo(query_, self._tokenizer)
        query_bag = query_info.bag_of_words
        for word in query_bag:
            candidate_indices.update(self._reverse_index.get(word,[]))
        for index in candidate_indices:
            paragraph_info = self._paragraph_info[index]
            score = self._score_function(self, query_info, paragraph_info)
            result.append((paragraph_info, score))
        result = sorted(result,key=lambda t: t[1], reverse=True)
        return result

    def _calc_idfs(self):
        self._idfs = [(word, self.idf(word)) for word in self.vocab]
        self._idfs_valid = True

    def _get_index(self, paragraph: Paragraph) -> Index:
        return paragraph.__hash__()

def test_with_parser() -> Processor:
    from qa_parser import QAParser
    parser = QAParser()
    qa_pairs = parser.parse_file('chatbot_qa.md')
    processor = Processor()
    for qa in qa_pairs:
        processor.process_paragraph(qa.question)
        #processor.process_paragraph(qa.answer)
    return processor

def test_with_md() -> Processor:
    processor = Processor()
    with open('chatbot_qa.md') as file:
        for line in file:
            if re.search('\w',line) is not None:
                processor.process_paragraph(line)

    return processor

def print_idfs(processor: Processor):
    idfs = list(processor.idfs.items())
    for paragraph in processor.paragraphs:
        print('*'*40)
        print(paragraph)
    print('*'*40)
    idfs = sorted(idfs, key=lambda t:t[1])
    i = 0
    cur = []
    for word,score in idfs:
        cur.append(f'---- {word:15} {score:5.3f}')
        i+=1
        if i % 4 == 0:
            print(' | '.join(cur))
            cur = []

def transform_query(query: str) -> str:
    query = query.lower()
    query = query.replace('you','Mono')
    return query

def run_queries(processor: Processor):
    q = ''
    while q != 'exit':
        print('*'*60)
        q = input('enter query: ')
        q = transform_query(q)
        results = processor.query(q)
        for p,s in results[:10]:
            print('paragraph:')
            print("\n".join('---- ' + l for l in smooth_split(p.paragraph, 80)))
            print(f'score: {s:6.2f}')

if __name__ == '__main__':
    processor = test_with_parser()
    #processor = test_with_md()
    run_queries(processor)

