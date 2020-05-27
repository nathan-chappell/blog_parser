# test.py

# Check the syntax of the samples file

import yaml
from pprint import pprint

def count_files():
    count = 0
    with open('samples.yml') as file:
        for line in file:
            if line[0] == '#': count += 1
    return count

def check_sample(sample) -> bool:
    keys = set([ "filename",
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

if __name__ == '__main__':
    with open('samples.yml') as file:
        y = yaml.full_load(file)
    # pprint(y)
    for i,sample in enumerate(y):
        if not check_sample(sample):
            print(f'BAD SAMPLE: {i:3}')
    qs = len(y)
    print(f'articles: {count_files()}, questions: {qs}')
