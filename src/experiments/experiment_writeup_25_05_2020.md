# Proposal and Overview of Experiments with Current QA System

This is intended to be a description of the experiments I intend to conduct over the following weeks.  What will be included is a description of the current system, data collection and analysis techniques, and what is expected to be done with the results.  Nothing stated here is final, and it is expected that from conducting experiments various notions will change about what should be measured.

# System Overview

The QA system currently parses data ("paragraphs") from the mono website dump, indexes them with ElasticSearch, receives a query from a web-api and returns predictions from the QA pipeline implemented in Haystack.  Therefore, there are four components:

* parsing
* indexing
* querying
* interface

The interface is not a concern for these experiments and will not be mentioned again.  The other components allow for varying degrees of flexibility, which will be described below.

## Parsing

The output of the parser is a set of "paragraphs," which are parts of the text of the blogs' html files.  Html tags are stripped, and any content not related to the article is generally discarded, however meta-data is extracted and kept with the paragraphs.  The paragraphs are contiguous sections of the text where whitespace is generally normalized in some fashion.  In some cases paragraphs are split and combined.  During previous testing, certain <code> examples are kept.

The purpose of paragraph splitting is to improve the prediction capabilities of haystack.  Firstly, the longer the expanse of text that the neural networks must search for answers, the longer they take to run.  Secondly, it is a reasonable assumption that providing the model with a concise representation of the answer it is looking for will help it perform better.  This results in a precision/ recall trade-off, however, since the more concise the representations, the harder it is to find them (more paragraphs leads to higher chance of providing the model with the wrong one).

The nature of paragraph splitting is a point of flexibility in the parsing scheme.  For example, if a paragraph is too short or too long, it may be split or concatenated with following paragraphs.  Currently, the functions pa\_chunk\_long and pa\_cat\_short are used for this purpose, and have had parameters set empirically to try to achieve a reasonable mean (and standard deviation of) paragraph size, measured in terms of word count.  Some obvious variations on parsing are:

* keep / remove sample code blocks
* change parameters for chunking/ concatenating

For simplicity, the only two variants on chunking/ contatentating to be modified at first will be:

* current chunking/ concatenating
* entire article is a paragraph

## Indexing

The indexer takes each paragraph and places it into its index with its metadata using the python elasticsearch client.  Currently, the index is created beforehand with mappings which define the metadata types and linguistic analyses conducted on the incoming paragraphs.  These "analyzers" impact the index and finally relevancy scores when the index processes a query.  The analysis takes place twice: once when the documents (paragraphs) are indexed, and again when the index is queried.  The points of variation to be investigated are:

* stemming
* stop-word removal
* synonym expansion
* relevancy algorithm/ parameters

The first two of these techniques should be applied uniformly to both the query and the index, synonym expansion should probably not be applied to indexing, and the relevancy algorithm can be modified independently.  To get initial results, stemming and stop-word removal will be tested turned on and off, synonym expanssion will be applied and not applied to the queries.  Two alternate values for _b_ and _k1_ will be chosen for the BM25 algorithm, and the DFR similarity will be tested with parameters "g,l,no".

## Querying

There are roughly two parts to the querying phase:

* query analysis
* prediction

### Query Analysis 

Query Analysis is a fairly broad topic, and more advanced techniques may include query categorization and user-state, however these will not be pursued here.  The extent of query analysis that will be tested for now is covered in the section on indexing, and is effectively lexical analysis + synonym expansion.

### Prediction

Prediction, then, consists of:

* answer prediction
* answer selection

### Answer Prediction 

Answer Prediction is the function of the nerual network architecture.  For this, there are different models with different pretrained parameters available for use, and also the opportunity to "fine tune" a model with your own data.  As of right now, "distilbert" is the model architecture being used with parameters pretrained on squad.  It will be interesting to see if different pretrained models perform siginicantly differently on the data set.  distilbert will be taken as the "baseline" or "standard," then at least three other models should be selected.  bert is distilbert, but with far more parameters, so it would be a useful candidate for comparison.  roberta seems to have interesting attentional output, so it is another.  Another path to model flexibility is to use the same model, with different pre-trained parameters.  There is a distilbert model trained on squad V2 readily available, so this one will also be tested (for reasons explained below).

### Answer Selection

Answer Selection is what to do with the results of prediction.  In general, it can be supposed that the output of a prediction is a conditional probability, i.e. p(span | d,q), which represents the probability that the _answer_ is given by the _span_, given that the answer to the query _q_ is in document _d_.  This makes choosing the best span from a given document for a given query simple: take the span with the highest probability.  However, it is no longer clear what to do if the answer is not actually in the document, or if you wish to compare answer-spans from different docuements.  This problem is addressed with SQuAD V2, where the dataset is enhanced with "tricky" questions for which there is no answer in the provided context.  This is the purpose of using the second distilbert model.

A technique to deal with answer-selection is rather important for the type of QA system we are building, however at this point I have not played around with any techniques.  Therefore, this experiment will be an opportunity to do so.  The __transformers__ library offers an opportunity to "handle no answers," so this functionality will be investigated.  There are separate approaches to answer selection (also referred to as "answer triggering" in some literatrue).  Two which have been identified as candidates here are LCLR (Question Answering Using Enhanced Lexical Semantic Models, Yih et al) and convolutional Neural Networks (Combining Graph-based Dependency Features with Convolutional Neural Network for Answer Triggering, Gupta et al).  There may be some less clever ways of doing answer selection, such as n-gram TF-IDF or something similar, which would be implementable using the tools available in ElasticSearch.  As for the other techniques, respective implementations have not been identified, so it is unclear the amount of effort needed to use them for testing.

## Summary of what is to be tested

Given the description above, here is a summary of how the system may be parameterized.  The experiment can be considered as running all questions through all combinations of parameters, that is the total parameter space is a cross product of the parameters.

[Parsing]

* {keep sample code, remove sample code}
* {current paragraph chunking, entire article is a paragraph}

[Indexing]

* {with stemming, without stemming}
* {with stopword removal, without stopword removal}

[Similarity]
* {BM25, DFR(g,l,no)}
* [BM25] {b=.8, b=.3}
* [BM25] {k1=1.2, k1=4}

[Query Analysis]
* {with synonym expansion, without synonym expansion}

[Answer Prediction - Model]
* {distilbert, distilbert SQuAD V2, bert, roberta}

[Answer Selection]
* (To be determined)

[Fine Tuning]
* (To be determined)

### Simplifications

Note that while experiments for answer selection is not currently determined, the results (model answers) can be collected in such a way that the answer selection can be tested and experimented with independently.  

All in all there are 2x2x2x2x(1+2x2)x2x4 = 640 configurations described above.  This is not a realistic scheme for experimentation, so the following simplification to the parameters space will be considered:

[Parsing]

* {remove sample code}
* {current paragraph chunking, entire article is a paragraph}

[Indexing]

* {with stemming, without stemming}
* {with stopword removal}

[Similarity]
* {BM25(b=.8,k1=1.2), DFR(g,l,no)}

[Query Analysis]
* {with synonym expansion, without synonym expansion}

[Answer Prediction - Model]
* {distilbert, distilbert-SQuAD-V2 (handle\_impossible\_answer=True), roberta}

This refined set of parameters gives 1x2x2x1x2x2x3 = 48 total configurations.  While still a large parameter space, this is computationally feasible and retains the parameters which are expected to be most interesting.  For the second distilbert model, the handle\_impossible\_answer flag will be turned on to investigate it's effect.

# Data Collection, Analysis, and Evaluation

In general, questions and answers will have to be extracted from the knowledge-base (blog posts), answers will have to be collected from the models, and comparisons will need to be made between the "ground-truth answers" and the answers given by the models.  The measurements considered in the papers on SQuAD and SQuAD 2.0 are "Exact Match" (EM) and F1.  F1 in this case is calculated from a "bag of tokens" comparison of the ground-truth answer and predicted answer.  These measurements are easily calculated given a question, answer, and prediction.  Not addressed in the SQuAD papers, but important to our experiments, will be the time to predict associated with the answer, as well as whether or not the indexing system retrieved the correct passage for the prediction component.  Information about the second and third best predictions may also be useful in attempting to improve the system, so that will also be collected.

## Questions

The sample set for testing will be collected as questions from the blog posts, with answers given as a span from the post.  Since indexing makes it hard to determine precisely which paragraph is being referenced by the model for prediction, the textual paragraph from which the span is taken will be part of the question's representation.

## Answers

The information necessary to make comparisons are the actual answers given by the model.  The output of Haystack includes the answer, a "context window," the document id (id in the index), as well as any associated meta data.  Additional data to include will be a "question id," as well as time it takes to get an answer.

## Analysis

Once the questions have been extracted, and the experiment has been programmed, data will be gathered.  The experiments will take place on ai-machine-2 due to it's superior capabilities.  Building the 16 different ElasticSearch indexes won't take much time.  It is expected that 240-400 questions will be gathered for testing (3-5 per blog post).  If it is estimated at 300 questions x 5 seconds / question x 48 question-sets, this gives 20 hours to complete the experiment.  Due to this long run time, results will be accumulated incrementally so analytical work can begin before all the results are gathered, and if some error or catastrophe should occur all results will not be lost.

Once gathered, F1 and EM scores will be calculated for the best answers given.  Charts displaying performance change with respect to different parameters will be generated (probably using matplotlib).

# Comments

Collecting the questions is expected to take a day or two.  Creating the framework for running the program will probably take 2-3 days.  For now the goal will be to be able to analyze the results next week (start the tests by close of business on Friday), and start considering methods of "answer selection" in the meantime.
