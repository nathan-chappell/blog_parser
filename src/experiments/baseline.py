# baseline.py

from experiments_base import add_parent_dir_to_path, Result, print_multi
from experiments_base import dumbStatusBar, yml_samples, Sample, is_test_run
from experiments_base import get_results_files
add_parent_dir_to_path()
from util import bannerfy, td2sec, smooth_split, get_log # type: ignore

from haystack.reader.transformers import TransformersReader # type: ignore
from haystack.database.base import Document # type: ignore

from typing import List, Union, Dict, Any
import yaml
from datetime import datetime
from logging import DEBUG

log = get_log(__file__,stderr=True)
log.setLevel(DEBUG)

def run_sample(sample: Sample, documents: List[Document], reader: TransformersReader) -> Result:
    result = Result.from_sample(sample)
    result.experiment_name = 'baseline'
    split = datetime.now()
    predictions = reader.predict(sample.question, documents)
    result.time = td2sec(datetime.now() - split)
    for p in predictions['answers']:
        result.add_prediction(p)
    return result

if __name__ == '__main__':
    reader = TransformersReader()

    pretty_file, yaml_file = get_results_files('baseline')

    results: List[Result] = []

    with open(yml_samples) as file:
        samples = yaml.full_load(file)

    if is_test_run():
        print(bannerfy(__file__ + ' TEST RUN'))
        _samples = samples[:3]
    else:
        _samples = samples

    n = len(_samples)

    inc = .2
    status = inc
    for sample in dumbStatusBar(_samples):
    #for i,sample in enumerate(_samples):
        log.debug(sample)
        document = Document(
            id='X', 
            text=sample.context,
            external_source_id=None, 
            question=None, 
            query_score=None, 
            meta=None,
        )
        result = run_sample(sample, [document], reader=reader)
        results.append(result)
        #print_multi(result,pretty_file,yaml_file)
        print_multi(result,pretty_file,None)
    print(yaml.dump(results),file=yaml_file)

    print(bannerfy(f'100% complete'))
