# classifier.py

# need to:
# parse the files ->
#
#   qa sets x category
#   ... null questions: <- random subset of overheard.txt
#
# fire up the distilbert
# train like in the article...

from typing import Tuple, List
from random import sample
import re

from nltk.corpus import webtext # type: ignore
from transformers import DistilBertTokenizer # type: ignore
from transformers import DistilBertForSequenceClassification # type: ignore
from transformers import DistilBertConfig # type: ignore
import torch
from torch import Tensor
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split # type: ignore

from qa_parser_2 import QAParser

g_device: torch.device

if torch.cuda.is_available():
    g_device = torch.device('cuda:0')
else:
    g_device = torch.device('cpu')

#
# for now we have four (not three, not five) categories.
#
CATEGORIES = 4

def get_overheard_questions() -> List[str]:
    text = webtext.raw('overheard.txt')
    questions = re.findall(r'[^:?!.]*\?',text)
    questions = sample(questions,100)
    return list(map(str.strip,questions))

def get_questions_and_labels() -> List[Tuple[str,str]]:
    result: List[Tuple[str,str]] = []
    filename = 'chatbot_qa_2.md'
    parser = QAParser()
    parser_results = parser.parse_file(filename)
    for qa_set in parser_results.qa_sets:
        label = qa_set.metadata['section']
        for q in qa_set.questions:
            result.append((q, label))
    for q in get_overheard_questions():
        result.append((q,'overheard_set'))
    return result

def print_questions_and_labels():
    for q,l in get_questions_and_labels():
        print(f'{l:20} --- {q}')


def get_transformer_stuff():
    pre_trained_model = 'distilbert-base-uncased'
    tokenizer = DistilBertTokenizer.from_pretrained(pre_trained_model)
    model = DistilBertForSequenceClassification.from_pretrained(
                    pre_trained_model,
                    num_labels=CATEGORIES
                )
    if torch.cuda.is_available():
        model.cuda()
    #
    # take the parameters from the classifier and last layer only
    #
    params = [p for n,p in model.named_parameters() 
                if 'classifier' in n or 'layer.5' in n]
    optimizer = torch.optim.Adam(params, lr=.00001)
    return tokenizer, model, optimizer

tokenizer, model, optimizer = get_transformer_stuff()
#tokenizer = DistilBertTokenizer.from_pretrained(pre_trained_model)

pre_trained_model = 'distilbert-base-uncased'

def label_to_int(label: str) -> int:
    if label == 'BASIC & ABOUT THE COMPANY': return 0
    if label == 'SHOWCASE': return 1
    if label == 'PROIZVODI': return 2
    if label == 'overheard_set': return 3
    raise RuntimeError(f'unknown label: {label}')

#
# returns:
# train ids, train categories, test ids, test categories
#
def get_tensor_data() -> Tuple[List[Tensor], List[Tensor]]:
    token_lists = []
    labels = []
    labeled_qs = get_questions_and_labels()
    max_toks = 0
    for q,l in labeled_qs:
        tokens = tokenizer.tokenize(f'[CLS] {q} [SEP]')
        token_lists.append(tokens)
        max_toks = max(max_toks, len(tokens))
        labels.append(label_to_int(l))
    def _pad_toklist(tokens: List[str]) -> List[str]:
        return tokens + [tokenizer.pad_token]*(max_toks - len(tokens))
    def _pad_and_convert(tokens: List[str]) -> List[str]:
        return tokenizer.convert_tokens_to_ids(_pad_toklist(tokens))
    ids = list(map(_pad_and_convert, token_lists))
    #return TensorDataset(torch.tensor(ids), torch.tensor(labels))
    t_ids = torch.tensor(ids)
    t_labels = torch.tensor(labels)
    ids_split = train_test_split(t_ids, train_size=.1, random_state=123)
    labels_split = train_test_split(t_labels, train_size=.1, random_state=123)
    return ids_split, labels_split

print_questions_and_labels()
ids_split, labels_split = get_tensor_data()
training_dataset = TensorDataset(ids_split[0], labels_split[0])
eval_dataset = TensorDataset(ids_split[1], labels_split[1])

training_dataloader = DataLoader(training_dataset, batch_size=3) # type: ignore
eval_dataloader = DataLoader(eval_dataset)

def total_loss() -> float:
    loss: float = 0.
    for ids,labels in training_dataloader:
        loss_,_ = model(ids.to(g_device),labels=labels.to(g_device))
        loss += loss_.item()
    for ids,labels in eval_dataloader:
        loss_,_ = model(ids.to(g_device),labels=labels.to(g_device))
        loss += loss_.item()
    return loss

def train(epochs: int = 100):
    for epoch in range(epochs):
        print(f'training epoch: {epoch:03}')
        print(total_loss())
        for ids,labels in training_dataloader:
            loss,_ = model(ids.to(g_device),labels=labels.to(g_device))
            loss.backward()
            optimizer.step()

train()
print(total_loss())


