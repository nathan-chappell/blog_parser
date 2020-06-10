# classifier.py

# need to:
# parse the files ->
#
#   qa sets x category
#   ... null questions: <- random subset of overheard.txt
#
# fire up the distilbert
# train like in the article...

from typing import Tuple, List, Dict
from random import sample
import re
from pathlib import Path
import sys
if sys.version_info >= (3,8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from nltk.corpus import webtext # type: ignore

from transformers import DistilBertTokenizer # type: ignore
from transformers import DistilBertForSequenceClassification # type: ignore
from transformers import DistilBertConfig # type: ignore
from transformers.tokenization_utils import PreTrainedTokenizer # type: ignore

import torch
from torch import Tensor
from torch.nn import Module
from torch.optim.optimizer import Optimizer # type: ignore
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split # type: ignore

from qa_parser_2 import QAParser

DEVICE: torch.device

if torch.cuda.is_available():
    DEVICE = torch.device('cuda')
else:
    DEVICE = torch.device('cpu')
#
# for now we have four (not three, not five) categories.
#
CATEGORIES = 4
DISTILBERT_NAME = 'distilbert-base-uncased'
CHECKPOINTS_DIR = Path('checkpoints')
SUFFIX = 'distilbert.classifier.state_dict'

label_to_int: Dict[str,int] = {
    'BASIC & ABOUT THE COMPANY': 0,
    'SHOWCASE': 1,
    'PROIZVODI': 2,
    'overheard_set': 3,
}

int_to_label: Dict[int,str] = {
    0: 'BASIC & ABOUT THE COMPANY',
    1: 'SHOWCASE',
    2: 'PROIZVODI',
    3: 'overheard_set',
}

def get_overheard_questions() -> List[str]:
    text = webtext.raw('overheard.txt')
    questions = re.findall(r'[^:?!.]*\?',text)
    questions = sample(questions,50)
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

def get_transformer_stuff() -> Tuple[PreTrainedTokenizer, Module, Optimizer]:
    tokenizer = DistilBertTokenizer.from_pretrained(DISTILBERT_NAME)
    model = DistilBertForSequenceClassification.from_pretrained(
                    DISTILBERT_NAME,
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
    return model, tokenizer, optimizer

#
# returns:
# train ids, train categories, test ids, test categories
#
def get_tensor_data(tokenizer: PreTrainedTokenizer) -> Tuple[List[Tensor], List[Tensor]]:
    token_lists = []
    labels = []
    labeled_qs = get_questions_and_labels()
    max_toks = 0
    for q,l in labeled_qs:
        tokens = tokenizer.tokenize(f'[CLS] {q} [SEP]')
        token_lists.append(tokens)
        max_toks = max(max_toks, len(tokens))
        labels.append(label_to_int[l])
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

def get_dataloaders(tokenizer: PreTrainedTokenizer):
    # print_questions_and_labels()
    ids_split, labels_split = get_tensor_data(tokenizer)
    training_dataset = TensorDataset(ids_split[0], labels_split[0])
    eval_dataset = TensorDataset(ids_split[1], labels_split[1])
    training_dataloader = DataLoader(training_dataset, batch_size=3) # type: ignore
    eval_dataloader = DataLoader(eval_dataset)
    return training_dataloader, eval_dataloader

def total_loss(model: Module, dataloader: DataLoader) -> Tensor:
    loss = torch.tensor(0.)
    with torch.no_grad():
        for ids,labels in dataloader:
            loss_,_ = model(ids.to(DEVICE),labels=labels.to(DEVICE))
            loss += loss_
    return loss

def print_loss(model: Module,
               training_dataloader: DataLoader,
               eval_dataloader: DataLoader):
    model.eval()
    train_loss = total_loss(model, training_dataloader)
    eval_loss = total_loss(model, eval_dataloader)
    fmt = 'train_loss: {loss1:8.3f} | eval_loss: {loss2:8.3f}'
    print(fmt.format(loss1=train_loss.item(), loss2=eval_loss.item()))
    model.train()

def train(model: Module,
          tokenizer: PreTrainedTokenizer,
          optimizer: Optimizer,
          epochs: int = 30):
    training_dataloader, eval_dataloader = get_dataloaders(tokenizer)
    for epoch in range(epochs):
        print(f'training epoch: {epoch:03}')
        print_loss(model, training_dataloader, eval_dataloader)
        for ids,labels in training_dataloader:
            loss,_ = model(ids.to(DEVICE),labels=labels.to(DEVICE))
            loss.backward()
            optimizer.step()
    print(f'--- Final Loss ---')
    print_loss(model, training_dataloader, eval_dataloader)

def get_probs(model: Module,
              tokenizer: PreTrainedTokenizer,
              query: str
              ) -> List[Tuple[str,float]]:
    tokens = tokenizer.tokenize(query)
    ids = tokenizer.convert_tokens_to_ids(tokens)
    logits = model(torch.tensor(ids, device=DEVICE).unsqueeze(0))
    probs = torch.nn.Softmax(dim=0)(logits[0].squeeze(0))
    result: List[Tuple[str,float]] = []
    for i,t in enumerate(probs):
        result.append((int_to_label[i],t.item()))
    return result

def query(model: Module, tokenizer: PreTrainedTokenizer):
    q = ''
    while q != 'exit':
        q = input('please enter query: ')
        for l,p in get_probs(model, tokenizer, q):
            print(f'{l[:15]:<18}: {p:5.3f}')
        print('_'*30)

def save_model(model: Module, prefix: str = ''):
    if prefix == '':
        n = len(list(CHECKPOINTS_DIR.glob(f'*.{SUFFIX}')))
        prefix = f'{n:03}'
    path = CHECKPOINTS_DIR / f'{prefix}.{SUFFIX}'
    torch.save(model.state_dict(), path)
    print(f'saved model to: {path}')

def load_model(model: Module, n=-1):
    if n == -1:
        count = len(list(CHECKPOINTS_DIR.glob(f'*.{SUFFIX}')))
        assert count > 0 and 'no saved state dicts!'
        path = CHECKPOINTS_DIR / f'{count-1}.{SUFFIX}'
    else:
        path = CHECKPOINTS_DIR / f'{n}.{SUFFIX}'
    model.load_state_dict(torch.load(path))
    print(f'successfully loaded model from {path}')

def get_model_interactive() -> Tuple[Module, PreTrainedTokenizer, Optimizer]:
    model, tokenizer, optimizer = get_transformer_stuff()
    train_new = ''
    while train_new != 'y' and train_new != 'n':
        train_new = input('train new model? [y/n]: ')
    if train_new == 'y':
        name = input('model name?: ')
        epochs = -1
        while epochs < 0:
            epochs_ = input('training epochs [int > 0]?: ')
            try:
                epochs = int(epochs_)
            except ValueError:
                continue
        train(model, tokenizer, optimizer, epochs)
        save_model(model, name)
    else:
        model_name = input('enter model name: ')
        load_model(model, model_name)
    return model, tokenizer, optimizer

if __name__ == '__main__':
    model, tokenizer, _ = get_model_interactive()
    query(model, tokenizer)
