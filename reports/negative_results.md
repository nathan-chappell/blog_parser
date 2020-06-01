This isn't a problem with the software per se, however I recently did some
experiments with the reader and got some troubling results.  

## Overview of Experiment

Parse blog posts from a website, and answer questions related to them.  I parsed out roughly 80 blog posts and indexed them in ElasticSearch.  I broke up the blog posts too ensure that no paragraph added to the index was "too short" or "too long."  Then I gathered about 90 questions, whose answers could be found within spans of the blog posts (as per SQuAD).  I wanted to see how the finder (using a TransformersReader and the ElasticSearch index for IR) would perform.  

## Evaluation  

For each question there was an associated "context window" which generally contained enough information to answer the question, but usually also some information not related to the question.  To get a baseline, I ran the Finder against the questions with their associated context (for this I made a "Dummy-Retriever" class which would only return the relevant context).  Then I calculated F1 scores as per the original SQuAD paper:

[real answer,predicted answer -> bag of words -> harmonic mean(precision, recall)]

The scores were encouraging, with a mean of roughly .75 (which is good, considering I didn't review the QA/context set and I've never created a data set for this type of experiment before).  Before testing against the real Finder, I did a couple of "manual tests."  I was immediately concerned that the Finder was not doing well, and it was due to it returning answers from the wrong blogs (and in general, completely non-sensical answers).

I first thought it could be an issue with the index, but it turned out that the index was behaving exactly as desired.  It turned out that the span "probabilities" returned from Reader were giving higher "probabilities" for the spans coming from the wrong blogs.  As far as I can tell, if the softmax layers results are to be interpreted as probabilities, then they must be interpreted as conditional probabilities, conditioned on the correct answer being in the given context (or perhaps no answer, depending on how the model is trained, for example against SQuAD v2).  Therefore, they are not directly comparable, and the "answer selection" step implemented in the TransformersReader is a sort of "naive heuristic."

I wanted to test the efficacy of this heuristic, so I set up my experiment to test the questions against the finder, where the parameter in the finder __top\_k_\retriever__ assumed values in {1,2,4} (I also ran the experiment with different analyses performed for indexing, however their observed effects were somewhat less definitive).  The best mean F1 for __top\_k_\retriever__ == 1 was .654, while for __top\_k_\retriever__ == 4 was .411, while the mean probability scores for the probability of the accepted prediction was .469 and .717, respectively.  What was previously observed held true in the mean, that a higher f1
