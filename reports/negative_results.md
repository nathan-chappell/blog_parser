# Results of the Experiments from last Week

Last week I ran some tests with the indexing system built for the blog posts on the mono website.  The results indicate that the current heuristic being employed by the Haystack software may be bad, and that indexing techniques seem to introduce less variance than answer selection.

## Overview of Experiment

The overall objective is to parse blog posts from a website, and answer questions related to them.  I parsed out roughly 80 blog posts and indexed them in ElasticSearch.  I broke up the blog posts too ensure that no paragraph added to the index was "too short" or "too long."  Then I gathered about 90 questions, whose answers could be found within spans of the blog posts (as per SQuAD).  I wanted to see how the finder (using a TransformersReader and the ElasticSearch index for IR) would perform.  

## Evaluation  

For each question there was an associated "context window" which generally contained enough information to answer the question, but usually also some information not related to the question.  To get a baseline, I ran the Finder against the questions with their associated context (for this I made a "Dummy-Retriever" class which would only return the context associated with a question).  Then I calculated F1 scores as per the original SQuAD paper:

"Comment: Calculating F1"

HarmonicMean(a,b):
    "Comment: Calculates average ratios.  See wikipedia for more information"
    return 2 / (1/a + 1/b)

Recall(truth, guess):
    "Comment: How much of the truth did you guess?"
    return |intersection(truth,guess)| / |truth|

Precision(truth, guess):
    "Comment: How much of what you guessed was the truth?"
    return |intersection(truth,guess)| / |guess|

F1(answer, prediction):
    let answer' = set of words in answer
    let prediction' = set of words in prediction
    return harmonicMean(
                Recall(answer',prediction'),
                Precision(answer',prediction')
            )

The scores were encouraging, with a mean of roughly .75 (which is good, considering I didn't review the QA/context set and I've never created a data set for this type of experiment before).  Before testing against the real Finder, I did a couple of "manual tests."  I was immediately concerned that the Finder was not doing well, and it was due to it returning answers from the wrong blogs (and in some cases, completely nonsensical answers).

I first thought it could be an issue with the index, but I found that the index was behaving exactly as desired.  It turned out that the span "probabilities" returned from Reader were giving higher "probabilities" for the spans coming from the wrong blogs.  As far as I can tell, if the softmax layers results are to be interpreted as probabilities, then they must be interpreted as conditional probabilities, conditioned on the correct answer being in the given context (or perhaps no answer, depending on how the model is trained, for example against SQuAD v2).  Therefore, they are not directly comparable, and the "answer selection" step implemented in the TransformersReader is a sort of "naive heuristic."

I wanted to test the efficacy of this heuristic, so I set up my experiment to test the questions against the finder, where the parameter in the finder __top-k-retriever__ assumed values in {1,2,4} (I also ran the experiment with different analyses performed for indexing, however their observed effects were somewhat less definitive).  The best mean F1 for __top-k-retriever__ == 1 was .654, while for __top-k-retriever__ == 4 was .411, while the mean probability scores for the probability of the accepted prediction was .469 and .717, respectively.  What was previously observed held true in the mean, that a higher f1 did not correspond to a higher probability.  The mean f1 and mean probability were negatively correlated, in fact, with a correlation coefficient of -.98.

## Analysis

Such a negative correlation is quite severe, so additional analysis was done in a "point-wise" manner.  For all queries, f1, pr (probability), recall (context vs retrieved document), and relevance (BM25 score from ElasticSearch-explain) were gathered.  The same statistics were gathered for all queries for all experiments (all values of top-k-retriever), and also for each value of k individually (results for each of the four separate indices were aggregated).  The actual results will be included at the end of this letter as an appendix, however some interesting trends are discussed here:

1. As mean(f1) goes up, so does correlation(f1, pr)
2. As mean(recall) goes up, so does correlation(pr, recall)
3. As mean(pr) goes up, mean(f1) goes down
4. As mean(recall) goes up, correlation(f1, recall) goes down

In prose, these results may be stated as follows:

1. If f1 is higher, pr provides a better indication of f1
2. If recall is higher, pr provides a better indication of recall
3. On its own, pr is a poor indication of f1
4. When recall is higher, it provides a worse indication of f1

### Explanation

Item (1) means that _given that we have the right answer_, a higher pr score corresponds to better accuracy.  This means that, when the model has the right answer, it gives a better pr score to answers it is more confident about.  Similarly for (2): if we have the right context, then the model will again be more confident.  Note that recall and f1 are not independent, so perhaps much of the confidence of higher recall can be explained by the confidence attributed to having a right answer. (1), (2), and (3) taken together tell us that using pr alone is a bad heuristic for answer selection.  While not 98% negatively correlated to f1 as in the case of the mean analysis, it is instructive to look at, for k=4, correlation(pr, recall) and correlation(f1, recall).

'''' top-k-retriever-4 | Correlation between pr and recall: 0.043
'''' top-k-retriever-4 | Correlation between f1 and recall: 0.814

Here it shows that recall and f1 are highly correlated (.81), which is what one would expect if the model is capable performing well (which it seems to be).  Given the right context, it can do a good job getting the right answer.  However, correlation(pr, recall) is .04.  This is what you would expect if pr and recall were almost independent.  If they were independent, then you would have confidence in answers varying independently of whether or not the right context was being observed.  Given that feeding the model the right context is the best way to get the right answer (otherwise what is the model doing?), this is again indicates that pr can't be taken seriously as an indicator of whether or not you have the right answer.

Item (4) may seem to indicate that maybe recall isn't a good indicator of f1, but it's important to observe that in this case we are almost certain that the model has the right context, and so a lower correlation here is due to the "noise" introduced by model's performance.  Basically, if we are almost certain that the model has the right context, then knowing that it has the right context doesn't tell us how well it will perform, and in this case pr in fact "steps-in" to explain some of the performance.

## Conclusion/ Further Research

From these results I am skeptical that the conditional probabilities given to answer spans should be used as heuristic for answer selection.  On this dataset, results are significantly improved by only considering the most relevant document retrieved, rather than looking for answers in multiple documents.  Although time was not discussed above, it should be no surprise that only considering the top retrieved document made the mean time decrease by a factor of roughly four (when compared with searching the top 4 documents).  

There are a number of reasons to be cautious about these conclusions.  First of all, a relatively small data set was used to gather these results.  It would be interesting to see if they still hold up at a larger scale.  One way to go about testing this would be to take the holdouts from SQuAD and compare pr statistics from assigned context other contexts which are relevant to the given question (what the meaning of relevance and recall in these situations would be of interest).

It is also worth noting that questions were created specifically for the data set in question.  In general (i.e. in a business setting), you cannot expect that a QA system will be given questions that can be answered exclusively by any document in a knowledge-base (or at all).  In this setting, answer selection is still quite relevant, and some heuristics must be employed.  While the results above imply that "go with your first instinct" is better than "look at a few documents and see how you feel," it remains open as to whether you can do better.  It would be interesting to investigate the distribution of "span-probabilities" that the model generates.  Perhaps distributional statistics such as entropy or information energy may give an indication of how likely it is that you have found a valid answer.  Perhaps there is some distribution that span probabilities assume when you do have a valid answer, and measuring divergence from this distribution is a good heuristic for choosing a best (or null) answer.

## Appendix

Here are the raw results of the experiment.
The results were gathered on 29, May, 2020.

The first set of results are the min/max/mean/std of f1, pr, and time for the QA system.  Different indexing techniques were used, including stemming and removal of stopwords.  The effects of these were not discussed, because there effects seem less pronounced, however they do seem to have more of an effect when comparing the top 4 retrieved documents.

Here are the results from the "mean analysis"

top-k-retriever-1 nostemmer-nostopword
f1                  [    0.000,     1.000,     0.654,     0.405]  (min/max/mean/std)
pr                  [    0.010,     0.983,     0.469,     0.289]  (min/max/mean/std)
time                [    0.153,     0.207,     0.183,     0.013]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-1 nostemmer-stopwords
f1                  [    0.000,     1.000,     0.632,     0.410]  (min/max/mean/std)
pr                  [    0.010,     0.983,     0.466,     0.291]  (min/max/mean/std)
time                [    0.151,     0.204,     0.182,     0.013]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-1 stemmer-nostopword
f1                  [    0.000,     1.000,     0.653,     0.407]  (min/max/mean/std)
pr                  [    0.010,     0.983,     0.468,     0.288]  (min/max/mean/std)
time                [    0.153,     0.208,     0.181,     0.013]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-1 stemmer-stopwords
f1                  [    0.000,     1.000,     0.635,     0.413]  (min/max/mean/std)
pr                  [    0.010,     0.983,     0.467,     0.289]  (min/max/mean/std)
time                [    0.152,     0.206,     0.177,     0.014]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-2 nostemmer-nostopword
f1                  [    0.000,     1.000,     0.548,     0.448]  (min/max/mean/std)
pr                  [    0.030,     0.983,     0.566,     0.259]  (min/max/mean/std)
time                [    0.310,     0.395,     0.359,     0.021]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-2 nostemmer-stopwords
f1                  [    0.000,     1.000,     0.501,     0.442]  (min/max/mean/std)
pr                  [    0.068,     0.996,     0.580,     0.255]  (min/max/mean/std)
time                [    0.319,     0.400,     0.369,     0.019]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-2 stemmer-nostopword
f1                  [    0.000,     1.000,     0.551,     0.445]  (min/max/mean/std)
pr                  [    0.068,     0.983,     0.570,     0.248]  (min/max/mean/std)
time                [    0.312,     0.396,     0.364,     0.019]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-2 stemmer-stopwords
f1                  [    0.000,     1.000,     0.497,     0.444]  (min/max/mean/std)
pr                  [    0.068,     0.983,     0.568,     0.247]  (min/max/mean/std)
time                [    0.310,     0.397,     0.360,     0.020]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-4 nostemmer-nostopword
f1                  [    0.000,     1.000,     0.396,     0.439]  (min/max/mean/std)
pr                  [    0.114,     0.988,     0.650,     0.227]  (min/max/mean/std)
time                [    0.617,     0.767,     0.717,     0.025]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-4 nostemmer-stopwords
f1                  [    0.000,     1.000,     0.408,     0.446]  (min/max/mean/std)
pr                  [    0.114,     0.996,     0.643,     0.234]  (min/max/mean/std)
time                [    0.655,     0.760,     0.717,     0.024]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-4 stemmer-nostopword
f1                  [    0.000,     1.000,     0.398,     0.447]  (min/max/mean/std)
pr                  [    0.208,     0.997,     0.665,     0.226]  (min/max/mean/std)
time                [    0.656,     0.773,     0.712,     0.024]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-4 stemmer-stopwords
f1                  [    0.000,     1.000,     0.411,     0.445]  (min/max/mean/std)
pr                  [    0.208,     0.996,     0.662,     0.222]  (min/max/mean/std)
time                [    0.655,     0.757,     0.717,     0.021]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
''''''''''''''''''''''''''''''''''''''''
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-1 nostemmer-nostopword
f1                  [    0.000,     1.000,     0.654,     0.405]  (min/max/mean/std)
pr                  [    0.010,     0.983,     0.469,     0.289]  (min/max/mean/std)
time                [    0.153,     0.207,     0.183,     0.013]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-1 stemmer-nostopword
f1                  [    0.000,     1.000,     0.653,     0.407]  (min/max/mean/std)
pr                  [    0.010,     0.983,     0.468,     0.288]  (min/max/mean/std)
time                [    0.153,     0.208,     0.181,     0.013]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-1 stemmer-stopwords
f1                  [    0.000,     1.000,     0.635,     0.413]  (min/max/mean/std)
pr                  [    0.010,     0.983,     0.467,     0.289]  (min/max/mean/std)
time                [    0.152,     0.206,     0.177,     0.014]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-1 nostemmer-stopwords
f1                  [    0.000,     1.000,     0.632,     0.410]  (min/max/mean/std)
pr                  [    0.010,     0.983,     0.466,     0.291]  (min/max/mean/std)
time                [    0.151,     0.204,     0.182,     0.013]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-2 stemmer-nostopword
f1                  [    0.000,     1.000,     0.551,     0.445]  (min/max/mean/std)
pr                  [    0.068,     0.983,     0.570,     0.248]  (min/max/mean/std)
time                [    0.312,     0.396,     0.364,     0.019]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-2 nostemmer-nostopword
f1                  [    0.000,     1.000,     0.548,     0.448]  (min/max/mean/std)
pr                  [    0.030,     0.983,     0.566,     0.259]  (min/max/mean/std)
time                [    0.310,     0.395,     0.359,     0.021]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-2 nostemmer-stopwords
f1                  [    0.000,     1.000,     0.501,     0.442]  (min/max/mean/std)
pr                  [    0.068,     0.996,     0.580,     0.255]  (min/max/mean/std)
time                [    0.319,     0.400,     0.369,     0.019]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-2 stemmer-stopwords
f1                  [    0.000,     1.000,     0.497,     0.444]  (min/max/mean/std)
pr                  [    0.068,     0.983,     0.568,     0.247]  (min/max/mean/std)
time                [    0.310,     0.397,     0.360,     0.020]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-4 stemmer-stopwords
f1                  [    0.000,     1.000,     0.411,     0.445]  (min/max/mean/std)
pr                  [    0.208,     0.996,     0.662,     0.222]  (min/max/mean/std)
time                [    0.655,     0.757,     0.717,     0.021]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-4 nostemmer-stopwords
f1                  [    0.000,     1.000,     0.408,     0.446]  (min/max/mean/std)
pr                  [    0.114,     0.996,     0.643,     0.234]  (min/max/mean/std)
time                [    0.655,     0.760,     0.717,     0.024]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-4 stemmer-nostopword
f1                  [    0.000,     1.000,     0.398,     0.447]  (min/max/mean/std)
pr                  [    0.208,     0.997,     0.665,     0.226]  (min/max/mean/std)
time                [    0.656,     0.773,     0.712,     0.024]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
top-k-retriever-4 nostemmer-nostopword
f1                  [    0.000,     1.000,     0.396,     0.439]  (min/max/mean/std)
pr                  [    0.114,     0.988,     0.650,     0.227]  (min/max/mean/std)
time                [    0.617,     0.767,     0.717,     0.025]  (min/max/mean/std)
''''''''''''''''''''''''''''''''''''''''
''''
'''' Correlation between pr and f1: -0.9841605840841612
''''

Here are the results from the "pointwise analysis"

''''
'''' all | mean f1: 0.524
'''' all | mean pr: 0.565
'''' all | mean recall: 0.735
'''' all | mean relevance: 16.963
''''
'''' all | Correlation between pr and f1: 0.172
'''' all | Correlation between pr and recall: 0.024
'''' all | Correlation between f1 and recall: 0.738
'''' all | Correlation between f1 and relevance: 0.362
'''' all | Correlation between pr and relevance: 0.091
'''' all | Correlation between relevance and recall: 0.475
''''
''''
'''' top-k-retriever-1 | mean f1: 0.643
'''' top-k-retriever-1 | mean pr: 0.467
'''' top-k-retriever-1 | mean recall: 0.871
'''' top-k-retriever-1 | mean relevance: 18.694
''''
'''' top-k-retriever-1 | Correlation between pr and f1: 0.375
'''' top-k-retriever-1 | Correlation between pr and recall: 0.187
'''' top-k-retriever-1 | Correlation between f1 and recall: 0.563
'''' top-k-retriever-1 | Correlation between f1 and relevance: 0.152
'''' top-k-retriever-1 | Correlation between pr and relevance: 0.236
'''' top-k-retriever-1 | Correlation between relevance and recall: 0.325
''''
''''
'''' top-k-retriever-2 | mean f1: 0.524
'''' top-k-retriever-2 | mean pr: 0.571
'''' top-k-retriever-2 | mean recall: 0.714
'''' top-k-retriever-2 | mean relevance: 17.127
''''
'''' top-k-retriever-2 | Correlation between pr and f1: 0.211
'''' top-k-retriever-2 | Correlation between pr and recall: 0.128
'''' top-k-retriever-2 | Correlation between f1 and recall: 0.753
'''' top-k-retriever-2 | Correlation between f1 and relevance: 0.357
'''' top-k-retriever-2 | Correlation between pr and relevance: 0.116
'''' top-k-retriever-2 | Correlation between relevance and recall: 0.478
''''
''''
'''' top-k-retriever-4 | mean f1: 0.403
'''' top-k-retriever-4 | mean pr: 0.655
'''' top-k-retriever-4 | mean recall: 0.621
'''' top-k-retriever-4 | mean relevance: 15.067
''''
'''' top-k-retriever-4 | Correlation between pr and f1: 0.158
'''' top-k-retriever-4 | Correlation between pr and recall: 0.043
'''' top-k-retriever-4 | Correlation between f1 and recall: 0.814
'''' top-k-retriever-4 | Correlation between f1 and relevance: 0.473
'''' top-k-retriever-4 | Correlation between pr and relevance: 0.107
'''' top-k-retriever-4 | Correlation between relevance and recall: 0.515
''''
