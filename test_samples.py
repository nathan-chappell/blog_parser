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

if __name__ == '__main__':
    with open('samples.yml') as file:
        y = yaml.full_load(file)
    pprint(y)

    qs = len(y)
    print(f'articles: {count_files()}, questions: {qs}')
