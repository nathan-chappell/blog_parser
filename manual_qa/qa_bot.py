# qa_bot.py

from typing import List, Tuple, Dict
from pprint import pprint

from nltk import wordnet # type: ignore

from util import get_logger
from qa_parser import QAParser, QAPair
from processor import Paragraph, Processor, NaiveTokenizer
from processor import ScoreFunctions

# Bot will have a processor for questions, and a processor for answers,
# getting different scores and combining them in interesting ways

# 
# TODO: inject this into the bot
#
def transform_query(query: str) -> str:
    query = query.lower()
    query = query.replace('are you','is mono')
    query = query.replace('you','Mono')
    return query

class QAPairBot:
    q_processor: Processor
    a_processor: Processor
    qa_pairs: List[QAPair]

    def __init__(self, qa_pairs: List[QAPair]):
        self.qa_pairs = qa_pairs
        self.q_processor = Processor(
                            tokenizer=NaiveTokenizer(),
                            score_function=ScoreFunctions.f1_weighted_score
                        )
        self.a_processor = Processor(
                            tokenizer=NaiveTokenizer(),
                            score_function=ScoreFunctions.sum_idf_score
                        )
        for i,pair in enumerate(qa_pairs):
            self.q_processor.process_paragraph(
                    pair.question,
                    metadata={'bot_index':i}
            )
            self.a_processor.process_paragraph(
                    pair.answer,
                    metadata={'bot_index':i}
            )

    def query(self, query_: str) -> List[Tuple[QAPair,float]]:
        # Parameters for "algorithm"
        top_k_processor = 5
        top_k_bot = 3
        a_list_scale = .4

        print(f'----- got query: {query_}')
        query_ = transform_query(query_)
        print(f'----- transformed: {query_}')

        q_list = self.q_processor.query(query_)[:top_k_processor]
        a_list = self.a_processor.query(query_)[:top_k_processor]

        # print('q_list: ' + '/'*40)
        # pprint(q_list)
        # print('a_list: ' + '/'*40)
        # pprint(a_list)

        tally: Dict[int, float] = {}
        for paragraph_info, score in q_list:
            bot_index = paragraph_info.metadata['bot_index']
            tally.setdefault(bot_index,0.)
            tally[bot_index] += score
        for paragraph_info, score in a_list:
            bot_index = paragraph_info.metadata['bot_index']
            tally.setdefault(bot_index,0.)
            tally[bot_index] += a_list_scale*score
        result = list(map(lambda it: (self.qa_pairs[it[0]], it[1]), tally.items()))
        result = sorted(result,key=lambda t:t[1], reverse=True)
        return result[:top_k_bot]

    def dump_all_pairs(self):
        for pair in self.qa_pairs:
            print('')
            print(pair)

    def test_run(self):
        q = ''
        while q != 'exit':
            print('-'*40)
            print(' '*40)
            q = input('please enter query: ')
            for a in self.query(q):
                print(' '*40)
                print(a)
                print('_'*40)

if __name__ == '__main__':
    filename = 'chatbot_qa_1.md'
    parser = QAParser()
    qa_pairs = parser.parse_file(filename)
    print(f'pairs parsed: {len(qa_pairs)}')
    bot = QAPairBot(qa_pairs)
    #bot.dump_all_pairs()
    bot.test_run()
