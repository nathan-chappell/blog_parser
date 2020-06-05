# score_functions.py

from typing import Callable, Set, Any
from statistics import harmonic_mean
from logging import INFO

from util import Protocol, get_logger
from paragraph_info import ParagraphInfo

log = get_logger(__file__)
#log.setLevel(INFO)

Score = float

class IdfCalculator(Protocol):
    def idf(self, word: str) -> Score: ...

class ScoreFunction(Protocol):
    def __call__(
            self, 
            idf_calculator: IdfCalculator,
            query: ParagraphInfo,
            paragraph: ParagraphInfo
        ) -> Score: ...

def f1(l: Set[Any], r: Set[Any]):
    count_l = len(l)
    count_r = len(r)
    if count_l == 0 and count_r == 0:
        return 1
    elif count_l == 0 or count_r == 0:
        return 0
    count_inter = len(l.intersection(r))
    if count_inter == 0:
        return 0
    return harmonic_mean([count_inter/count_l, count_inter/count_r])

def sum_idf_score(
            idf_calculator: IdfCalculator,
            query: ParagraphInfo,
            paragraph: ParagraphInfo
        ) -> Score:
    common_words = query.bag_of_words.intersection(paragraph.bag_of_words)
    common_idfs = [(idf_calculator.idf(word),word) for word in common_words]
    log.debug("\ncommon idfs:\n"+"\n".join(map(str,common_idfs))+"\n")
    score = sum([score for score,_ in common_idfs])
    log.debug(f'query: {query.paragraph}')
    log.debug(f'paragraph: {paragraph.paragraph}')
    log.debug(f"score: {score}\n")
    return score

def f1_weighted_score(
            idf_calculator: IdfCalculator,
            query: ParagraphInfo,
            paragraph: ParagraphInfo
        ) -> Score:
    sum_score = sum_idf_score(idf_calculator,query,paragraph)
    f1_ = f1(query.bag_of_words, paragraph.bag_of_words)
    adjustment_threshold = .6
    adjusted_f1_score = adjustment_threshold + (1-adjustment_threshold)*f1_
    if f1_ > .9: adjusted_f1_score += 1
    elif f1_ > .75: adjusted_f1_score += .2
    else: f1_ = .75
    score = adjusted_f1_score*sum_score
    log.debug(f'f1 weight: {f1_}')
    log.debug(f"score: {score}\n")
    return score

