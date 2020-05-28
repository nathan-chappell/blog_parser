# baseline.py

from experiments_base import add_parent_dir_to_path, Result, print_multi, dumbStatusBar
add_parent_dir_to_path()
from util import bannerfy, td2sec, smooth_split # type: ignore

from haystack.reader.transformers import TransformersReader # type: ignore
from haystack.database.base import Document # type: ignore

from typing import List, Union, Dict, Any
import yaml
from datetime import datetime
from tqdm import tqdm

def run_sample(sample: Dict[str,Any], documents: List[Document], reader: TransformersReader) -> Result:
    question = sample['question']
    answer = sample['answer']
    context = document.text
    result = Result(question, answer, context)
    split = datetime.now()
    predictions = reader.predict(question, documents)
    result.time = td2sec(datetime.now() - split)
    for p in predictions['answers']:
        result.add_prediction(p)
    return result

if __name__ == '__main__':
    reader = TransformersReader()

    pretty_filename = 'initial_results_pretty.txt'
    pretty_file = open(pretty_filename,mode='w')
    yaml_filename = 'initial_results.yml'
    yaml_file = open(yaml_filename,mode='w')

    results = []

    samples_filename = 'samples.yml'
    with open(samples_filename) as file:
        samples = yaml.full_load(file)

    import os
    if 'EXPERIMENTS_TEST' in os.environ.keys():
        TEST_RUN = True
    else:
        TEST_RUN = False

    if TEST_RUN:
        print(bannerfy(__file__ + ' TEST RUN'))
        _samples = samples[:3]
    else:
        _samples = samples

    n = len(_samples)

    inc = .2
    status = inc
    for sample in dumbStatusBar(_samples):
    #for i,sample in enumerate(_samples):
        document = Document(
            id='X', 
            text=sample['context'],
            external_source_id=None, 
            question=None, 
            query_score=None, 
            meta=None,
        )
        result = run_sample(sample, [document], reader=reader)
        results.append(result)
        print_multi(result,pretty_file,yaml_file)
        #if (i / n > status):
            #status += inc
            #pct = round(i/n*100)
            #print(bannerfy(f'{pct}% complete'))

    print(bannerfy(f'100% complete'))
    yaml_file.close()
    pretty_file.close()
