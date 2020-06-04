# qa_bot.py

from typing import List, Tuple, Dict, DefaultDict
from collections import defaultdict
import random
import re
from logging import DEBUG

from nltk.corpus import wordnet as wn # type: ignore
from nltk.chat.eliza import eliza_chatbot

from util import get_logger
from qa_parser_2 import QAParser
from parser_result import ParserResult, ParserQASet
from processor import Paragraph, Processor, NaiveTokenizer, ParagraphInfo
from processor import ScoreFunctions, Score, BiGramTokenizer

log = get_logger(__file__)
log.setLevel(DEBUG)

# Bot will have a processor for questions, and a processor for answers,
# getting different scores and combining them in interesting ways

Index = int

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
    q_processor: Processor
    a_processor: Processor
    parser_result: ParserResult

    # TODO parameterize this helpfully
    def __init__(self, parser_result: ParserResult):
        self.parser_result = parser_result
        self.reset_processors()
        self.prepare()

    # TODO parameterize this helpfully
    def reset_processors(self):
        self.q_processor = Processor(
                            tokenizer=NaiveTokenizer(),
                            #tokenizer=BiGramTokenizer(),
                            score_function=ScoreFunctions.f1_weighted_score
                        )
        self.a_processor = Processor(
                            tokenizer=NaiveTokenizer(),
                            score_function=ScoreFunctions.sum_idf_score
                        )

    def prepare(self):
        for i,qa_set in enumerate(self.parser_result.qa_sets):
            for question in qa_set.questions:
                self.q_processor.process_paragraph(
                    question,
                    metadata={'bot_index':i}
                )
            for answer in qa_set.answers:
                self.a_processor.process_paragraph(
                    answer,
                    metadata={'bot_index':i}
                )

    def greeting(self) -> str:
        return self.parser_result.greeting_set.get_random_greeting()

    def combine_processor_scores(
            self,
            q_list: List[Tuple[ParagraphInfo,Score]],
            a_list: List[Tuple[ParagraphInfo,Score]],
            a_list_scale: float
    ) -> List[Tuple[ParserQASet,float]]:

        q_max: DefaultDict[Index, Score] = defaultdict(float)
        a_max: DefaultDict[Index, Score] = defaultdict(float)

        for paragraph_info, score in q_list:
            bot_index = paragraph_info.metadata['bot_index']
            q_max[bot_index] = max(q_max[bot_index],score)

        for paragraph_info, score in a_list:
            bot_index = paragraph_info.metadata['bot_index']
            a_max[bot_index] = max(a_max[bot_index],score)

        summed: DefaultDict[Index, Score] = defaultdict(float)
        for k,v in q_max.items(): summed[k] = v
        for k,v in a_max.items(): summed[k] += a_list_scale*v

        info_scores = [(self.parser_result.qa_sets[i],score) 
                       for i,score in summed.items()]
        result = sorted(info_scores,key=lambda t:t[1], reverse=True)
        return result

    def null_response(self, query_: str) -> str:
        #return "null response"
        return f'[ELIZA] {eliza_chatbot.respond(query_)})'

    def choose_response(
            self, 
            query_: str, 
            candidates: List[Tuple[ParserQASet,Score]]
            ) -> str:
        # TODO: choose better parameters
        log.info(f"top five candidates:\n{candidates[:5]}")
        threshold = 2.
        epsilon = .3
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
        top_k_processor = 5
        top_k_bot = 3
        a_list_scale = .4

        log.info(f'----- got query: {query_}')
        query_ = transform_query(query_)
        log.info(f'----- transformed: {query_}')

        q_list = self.q_processor.query(query_)[:top_k_processor]
        a_list = self.a_processor.query(query_)[:top_k_processor]

        combined = self.combine_processor_scores(q_list, a_list, a_list_scale)
        #return combined[:top_k_bot]
        chosen = self.choose_response(query_, combined)
        return chosen

    def test_run(self):
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

if __name__ == '__main__':
    filename = 'chatbot_qa_2.md'
    parser = QAParser()
    parser_result = parser.parse_file(filename)
    print(f'sets parsed: {len(parser_result.qa_sets)}')
    bot = QABot(parser_result)
    print(bot.parser_result)
    bot.q_processor.print_idfs()
    print("__________________________\n"*3)
    bot.a_processor.print_idfs()
    bot.test_run()
