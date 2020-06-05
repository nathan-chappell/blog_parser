# paragraph_info.py

from typing import Set, DefaultDict, Dict, Any
from collections import defaultdict
from pprint import pformat

from analyzer import Paragraph, Analyzer

BagOfWords = Set[str]

class ParagraphInfo:
    """Keeps track of tf counts for paragraph to avoid many recomputations"""
    _tfs: DefaultDict[str,int]
    _paragraph: Paragraph
    _metadata: Dict[str,Any]

    def __init__(self, 
                 paragraph: Paragraph,
                 analyzer: Analyzer,
                 metadata: Dict[str,Any] = {}
            ):
        self._paragraph = paragraph
        self._tfs = defaultdict(int)
        words = analyzer(paragraph)
        for word in words:
            self._tfs[word] += 1
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
        return "\n".join(strs) + ')'


