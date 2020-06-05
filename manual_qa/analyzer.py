# analyzer.py

from functools import reduce
from typing import TypeVar, Callable
import re
from typing import List, Callable, Any, cast, Dict
import yaml

from nltk.stem import WordNetLemmatizer # type: ignore
from nltk.tokenize import RegexpTokenizer, MWETokenizer # type: ignore
from nltk.corpus import wordnet as wn # type: ignore

from util import reduce_transforms, Protocol, Transform

Paragraph = str
Token = str
TokenStream = List[Token]

#
# While defining the following types as Callables is a bit more concise and
# says directly what I want, defining them as Protocols plays much nicer with
# mypy
#

# Tokenizer = Callable[[Paragraph],TokenStream]
# TokenFilter = Callable[[TokenStream],TokenStream]
# Analyzer = Callable[[Paragraph],List[Token]]

class Tokenizer(Protocol):
    def __call__(self, paragraph: Paragraph) -> TokenStream: ...

class TokenFilter(Protocol):
    def __call__(self, token_stream: TokenStream) -> TokenStream: ...

class Analyzer(Protocol):
    def __call__(self, paragraph: Paragraph) -> List[Token]: ...

def naive_tokenizer(paragraph: Paragraph) -> TokenStream:
    return re.split('\W+', paragraph)

class MyRegexpTokenizer:
    tokenizer: RegexpTokenizer

    def __init__(self):
        regexps = [
            r'\w+-\w+',
            r'\w+n\'t',
            r'\w+\'s',
            r'\w+',
        ]
        self.tokenizer = RegexpTokenizer('|'.join(regexps))

    def __call__(self, paragraph: Paragraph) -> TokenStream:
        return self.tokenizer.tokenize(paragraph)

def nonwords_filter(token_stream: TokenStream) -> TokenStream:
    return list(filter(lambda s: re.match('\w+',s), token_stream))

def lowercase_filter(token_stream: TokenStream) -> TokenStream:
    return list(map(lambda s: s.lower(), token_stream))

def morphy_filter(token_stream: TokenStream) -> TokenStream:
    result: TokenStream = []
    for word in token_stream:
        morph = wn.morphy(word)
        if morph:
            result.append(morph)
        else:
            result.append(word)
    return result

class MWEFilter:
    tokenizer: MWETokenizer
    def __init__(self):
        mwes = [
            ('what','is'),
            ('machine','learning'),
            ('deep','learning'),
            ('data','science'),
            ('artificial','intelligence'),
            ('work','with'),
        ]
        self.tokenizer = MWETokenizer(mwes)

    def __call__(self, token_stream: TokenStream) -> TokenStream:
        return self.tokenizer.tokenize(token_stream)

def hyphen_to_under_filter(token_stream: TokenStream) -> TokenStream:
    def do_replace(s: str) -> str:
        return s.replace('-','_')
    return list(map(do_replace, token_stream))

class SynMapFilter:
    synmap: Dict[str,str]

    def __init__(self, synmap: Dict[str,str]):
        self.synmap = synmap

    def __call__(self, token_stream: TokenStream) -> TokenStream:
        def do_replace(s: str) -> str:
            if s in self.synmap:
                return self.synmap[s]
            else:
                return s
        return list(map(do_replace, token_stream))

with open('synonyms.yml') as file:
    local_synmaps: Dict[str, str] = yaml.full_load(file)

class BiGramTokenizer:
    """Naive tokenization followed bi bigram joining"""
    naive_tokenizer: MyRegexpTokenizer

    def __init__(self):
        self.naive_tokenizer = MyRegexpTokenizer()

    def __call__(self, paragraph: Paragraph) -> TokenStream:
        naive_result: Any = self.naive_tokenizer(paragraph)
        result: List[str] = []
        result.extend(naive_result)
        for i in range(len(naive_result)-1):
            result.append(f'{naive_result[i]}-{naive_result[i+1]}')
        return list(result)

class BasicAnalyzer:
    """Tokenize and apply filters"""
    tokenizer: Tokenizer
    token_filters: List[TokenFilter]

    def __init__(self,
                 tokenizer: Tokenizer, 
                 token_filters: List[TokenFilter]
                ):
        self.tokenizer = tokenizer
        self.token_filters = token_filters

    def __call__(self, paragraph: Paragraph) -> List[Token]:
        token_stream: TokenStream = self.tokenizer(paragraph)
        token_filters = cast(List[Transform[List[str]]], self.token_filters)
        return reduce_transforms(token_filters, token_stream)

class StandardAnalyzer(BasicAnalyzer):
    """Provide a convenient Analyzer class"""
    def __init__(self):
        super().__init__(
            MyRegexpTokenizer(),
            [ 
                lowercase_filter, 
                SynMapFilter(local_synmaps),
                MWEFilter(),
                hyphen_to_under_filter,
                # include again to synmap multi-word expressions (mwes)
                # e.g.: work with -> [work,with] -> work_with -> use
                SynMapFilter(local_synmaps),
                morphy_filter,
            ],
        )

