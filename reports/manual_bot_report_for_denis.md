Hey Denis, I got the manual qa bot to a reasonable state I think.

I'm going to go home, and I'll plan on taking a look at those things you sent this weekend. I'll also get the summary done this weekend as well. As far as the manual qa bot goes, I put some "NLP" into it using some utilities from the python nltk (Natural Language Toolkit).

Nothing too sexy, although I do use a little bit of wordnet capabilites (they have some "dumb" transformation tool that deals with transforming plurals and verb conjugations and some other stuff). It basically just uses IDF scores to rank known questions and answers (it uses a weighted sum of their scores), then chooses an answer randomly among those that make a threshold (based off of the top score and a minimal score). If no answer makes the minimal score, it lets ELIZA (an implementation from the nltk) give a generic answer.

I put in some very rudimentary support for dealing with synonyms, basically a yaml file which has a word and the word it should be mapped to (for example, "ai" get changed to "artificial intelligence" after tokenization and before further processing). 

All this is glued together in an "analysis pipeline," modelled after the way it is done in ElasticSearch, although implementing it myself allows for some flexibility that would probably just be a pain to get out of using ElasticSearch directly.

I made it "smart" by training it on some language corpora that is stored in the nltk. Basically, after it indexes the questions and answers, it will take a paragraph and put term occurences in a "hidden index." This hidden index affects calculating IDF (by adding to occurences and total documents), but the actual string data is discarded. This allows for "tuning" IDF scores (so a word like "do" or "what" gets a low score, as it should). This is an example of something that I don't know how to really achieve in a straightforward way using ElasticSearch.

I think that the next most useful thing will be to put an interface on it that not only serves queries, but allows for someone to add questions to it's known question set. For example, when I ask "do you use machine learning?", right now it's not clear which of the following (paraphrased) answers the bot should give:

* Our team is well experienced in developing advanced web and mobile solutions using artificial intelligence, machine learning, deep learning, and data science.

* Our team can build all kinds of software systems according to your specifications using Python and the accompanying tech stack. We will also use Python in distributed environments (for example, microservice architecture) for components or services that need its unique advantages (machine learning, data science, etc.).

The reason this is ambiguous is mostly because neither one of them feature the term "machine learning" in their corresponding question sets. I would guess that the first one is preferable, but it's probably easier to just tell the bot that directly than let it guess.

There are probably some more "smart" techniques to be baked into this type of processing (interesting uses of Bert or something like it). It's not clear what the priority should be though, more advanced stuff, or an interface that allows for tweaking the bot and observing its behavior (logs of conversations and score calculations...).

There is also a question of if we'd like to incorporate this bot into the BotFramework. If we just want to "freeze" a well performing bot with all its knowledge and upload it to azure I'm pretty sure that we can, but I don't know if we'd rather just use Microsoft to forward messages to a hosted server and deal with them here. If we want to avoid the BotFramework altogether, I can look up some API (like facebook or slack) and get something working directly. It will be a little annoying, but not without some benefits...

That's enough of my rambling, I'll get the summary to you this weekend.
