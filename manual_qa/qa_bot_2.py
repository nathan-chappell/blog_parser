# qa_bot.py

from typing import List, Tuple, Dict, DefaultDict, cast
from collections import defaultdict
import random
import re
from logging import DEBUG

from nltk.corpus import wordnet as wn # type: ignore
from nltk.chat.eliza import eliza_chatbot # type: ignore

from util import get_logger
from qa_parser_2 import QAParser
from parser_result import ParserResult, ParserQASet
from index import Index, InfoIndex, StandardIndex, TrainableIndex
from paragraph_info import ParagraphInfo
from score_functions import Score, ScoreFunction
from score_functions import sum_idf_score, f1_weighted_score
from analyzer import Analyzer, StandardAnalyzer, Paragraph

log = get_logger(__file__)
log.setLevel(DEBUG)

# Bot will have a index for questions, and a index for answers,
# getting different scores and combining them in interesting ways

# 
# TODO: inject this into the bot
#
def transform_query(query: str) -> str:
    query = query.lower()
    query = re.sub('are you ','is mono ',query)
    query = re.sub('do you ','does mono ',query)
    query = re.sub(' you ','mono',query)
    return query

class QABot:
    q_index: Index
    a_index: Index
    parser_result: ParserResult

    # TODO parameterize this helpfully
    def __init__(self, parser_result: ParserResult):
        self.parser_result = parser_result
        self.reset_indexes()
        self.prepare()

    # TODO parameterize this helpfully
    def reset_indexes(self) -> None:
        q_analyzer = StandardAnalyzer()
        q_scorer = f1_weighted_score
        a_analyzer = StandardAnalyzer()
        a_scorer = f1_weighted_score

        self.q_index = TrainableIndex(q_analyzer, cast(ScoreFunction, q_scorer))
        self.a_index = TrainableIndex(a_analyzer, cast(ScoreFunction, a_scorer))

    def prepare(self) -> None:
        for i,qa_set in enumerate(self.parser_result.qa_sets):
            for question in qa_set.questions:
                self.q_index.index_paragraph(
                    question,
                    metadata={'bot_index':i}
                )
            for answer in qa_set.answers:
                self.a_index.index_paragraph(
                    answer,
                    metadata={'bot_index':i}
                )

    def greeting(self) -> str:
        return self.parser_result.greeting_set.get_random_greeting()

    def combine_index_scores(
            self,
            q_list: List[Tuple[ParagraphInfo,Score]],
            a_list: List[Tuple[ParagraphInfo,Score]],
            a_list_scale: float
    ) -> List[Tuple[ParserQASet,float]]:

        q_max: DefaultDict[InfoIndex, Score] = defaultdict(float)
        a_max: DefaultDict[InfoIndex, Score] = defaultdict(float)

        for paragraph_info, score in q_list:
            bot_index = paragraph_info.metadata['bot_index']
            q_max[bot_index] = max(q_max[bot_index],score)

        for paragraph_info, score in a_list:
            bot_index = paragraph_info.metadata['bot_index']
            a_max[bot_index] = max(a_max[bot_index],score)

        summed: DefaultDict[InfoIndex, Score] = defaultdict(float)
        for k,v in q_max.items(): summed[k] = v
        for k,v in a_max.items(): summed[k] += a_list_scale*v

        info_scores = [(self.parser_result.qa_sets[i],score) 
                       for i,score in summed.items()]
        result = sorted(info_scores,key=lambda t:t[1], reverse=True)
        return result

    def null_response(self, query_: str) -> str:
        #return "null response"
        return f'[ELIZA] {eliza_chatbot.respond(query_)}'

    def choose_response(
            self, 
            query_: str, 
            candidates: List[Tuple[ParserQASet,Score]]
            ) -> str:
        # TODO: choose better parameters
        #log.info(f"top five candidates:\n{candidates[:5]}")
        for qa_set,score in candidates[:3]:
            print(f"Candidate score: {score}\n")
            print(qa_set)
            print('-'*20)
        threshold = 5
        epsilon = 1
        if len(candidates) == 0:
            return self.null_response(query_)
        max_score = candidates[0][1]
        if max_score < threshold:
            return self.null_response(query_)
        def pretty_close(pair: Tuple[ParserQASet,float]) -> bool:
            return pair[1] >= max_score - epsilon
        max_candidates = list(filter(pretty_close,candidates))
        selected = random.choice(max_candidates)
        return random.choice(list(selected[0].answers))

    #def query(self, query_: str) -> List[Tuple[ParserQASet,float]]:
    def query(self, query_: str) -> str:
        # Parameters for "algorithm"
        top_k_index = 5
        top_k_bot = 3
        a_list_scale = .8

        log.info(f'----- got query: {query_}')
        query_ = transform_query(query_)
        log.info(f'----- transformed: {query_}')

        q_list = self.q_index.query(query_)[:top_k_index]
        a_list = self.a_index.query(query_)[:top_k_index]

        combined = self.combine_index_scores(q_list, a_list, a_list_scale)
        #return combined[:top_k_bot]
        chosen = self.choose_response(query_, combined)
        return chosen

    def test_run(self) -> None:
        def dash(): print('-'*40)
        def nl(): print('')
        def under(): print('_'*40)

        print(self.greeting())
        dash()
        q = ''
        while q != 'exit':
            dash()
            nl()
            q = input('please enter query: ')
            nl()
            response = self.query(q)
            under()
            print(response)
            under()
            #for a in self.query(q):
                #nl()
                #print(a)
                #under()

def get_training_paragraphs() -> List[Paragraph]:
    paragraphs: List[Paragraph] = []

    from nltk.corpus import webtext
    text = webtext.raw('overheard.txt')
    paragraphs.extend(text.split("\n\n"))

    from nltk.corpus import brown 
    text = brown.raw(categories='news')
    text = re.sub('/\S+','',text)
    paragraphs.extend(text.split("\n\n"))

    log.info(f'len(paragraphs) = {len(paragraphs)}')

    return paragraphs

def train_bot_indices(bot: QABot):
    paragraphs = get_training_paragraphs()
    if isinstance(bot.q_index, TrainableIndex):
        for paragraph in paragraphs:
            bot.q_index.train(paragraph)
    if isinstance(bot.a_index, TrainableIndex):
        for paragraph in paragraphs:
            bot.a_index.train(paragraph)

if __name__ == '__main__':
    filename = 'chatbot_qa_2.md'
    parser = QAParser()
    parser_result = parser.parse_file(filename)
    print(f'sets parsed: {len(parser_result.qa_sets)}')
    bot = QABot(parser_result)
    #print(bot.parser_result)
    bot.q_index.print_idfs()
    print("__________________________\n"*3)
    bot.a_index.print_idfs()
    train_bot_indices(bot)
    print("--------------------------\n"*3)
    bot.q_index.print_idfs()
    print("__________________________\n"*3)
    bot.a_index.print_idfs()
    bot.test_run()
