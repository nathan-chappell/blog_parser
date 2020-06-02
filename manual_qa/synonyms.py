# synonyms.py

# given a list of paragraphs (lists of words), come up with a reasonable base
# for a synonmy file for ElasticSearch.  The files will probably need to be
# manually reviewed

from util import is_test
from nltk import wordnet # type: ignore
from typing import List, Set, Dict, Tuple, Any
import re
from math import log

Paragraph = str
BagOfWords = Set[str]
#tokenizer = nltk.tokenize.NLTKTokenizer()

splitter = re.compile('\W+')
word_finder = re.compile('\w+')

def is_word(word: str) -> bool:
    return word_finder.match(word) is not None

def tokenize(words: str) -> List[str]:
    result: Any = None
    result = splitter.split(words)
    result = filter(is_word, result)
    result = map(lambda s: s.lower(), result)
    return list(result)

def get_bag(paragraph: Paragraph) -> BagOfWords:
    result: Any = None
    result = tokenize(paragraph)
    result = filter(lambda s: len(s) > 1, result)
    return set(result)

def calc_idf(df: int, n: int) -> float:
    return log((n+1.)/(df+.5))

class Processor:
    """Take a list of paragraphs, make a reverse index and vocab set"""
    paragraphs: List[Paragraph]
    reverse_index: Dict[str,List[int]]
    vocab: Set[str]

    def __init__(self, paragraphs: List[Paragraph] = []):
        self.paragraphs = []
        self.reverse_index = {}
        self.vocab = set()
        for paragraph in paragraphs:
            self.process_paragraph(paragraph)

    def process_paragraph(self, paragraph: Paragraph):
        index = len(self.paragraphs)
        self.paragraphs.append(paragraph)
        bag = get_bag(paragraph)
        self.vocab.update(bag)
        for word in bag:
            self.reverse_index.setdefault(word,[])
            self.reverse_index[word].append(index)

    def get_idfs(self) -> List[Tuple[str,float]]:
        idfs: List[Tuple[str,float]] = []
        n = len(self.paragraphs)
        for word in self.vocab:
            df = len(self.reverse_index[word])
            idfs.append((word,calc_idf(df,n)))
        return idfs

def test_with_parser() -> Processor:
    from qa_parser import QAParser
    parser = QAParser()
    qa_pairs = parser.parse_file('chatbot_qa.md')
    processor = Processor()
    for qa in qa_pairs:
        #processor.process_paragraph(qa.question)
        processor.process_paragraph(qa.answer)
    return processor

def test_with_md() -> Processor:
    processor = Processor()
    with open('chatbot_qa.md') as file:
        for line in file:
            if re.search('\w',line) is not None:
                processor.process_paragraph(line)

    return processor

if __name__ == '__main__':
    processor = test_with_parser()
    #processor = test_with_md()
    idfs = processor.get_idfs()
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

