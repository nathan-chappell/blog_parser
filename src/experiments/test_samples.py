# test.py

# Check the syntax of the samples file

from experiments_base import yml_samples
from experiments import Sample

import yaml
from pprint import pprint

def count_files():
    count = 0
    with open('samples.yml') as file:
        for line in file:
            if line[0] == '#': count += 1
    return count

def check_sample(sample) -> bool:
    keys = set([ 
        "filename",
        "article_title",
        "question",
        "answer",
        "context",
        ])
    missing_keys = keys - sample.keys()
    if missing_keys:
        print('missing keys: ',' '.join(missing_keys))
        return False
    return True

def get_sample(yml_dict) -> Sample:
    sample = Sample()
    sample.question = yml_dict['question']
    sample.answer = yml_dict['answer']
    sample.context = yml_dict['context']
    sample.article_title = yml_dict['article_title']
    sample.filename = yml_dict['filename']
    return sample

if __name__ == '__main__':
    with open('samples.yml') as file:
        y = yaml.full_load(file)
    # pprint(y)
    ymls = []
    for i,sample in enumerate(y):
        if not check_sample(sample):
            print(f'BAD SAMPLE: {i:3}')
        else:
            ymls.append(get_sample(sample))
    qs = len(y)
    print(f'articles: {count_files()}, questions: {qs}')
    with open(yml_samples,'w') as file:
        yaml.dump(ymls,file)
