# Item-Tokenization-Model for Shwapno retail

Dataset link: https://drive.google.com/drive/folders/1i9vpaq8qYk0oyV0LWJRT1EIL0S0hhevd?usp=share_link

## Word2Vec documentation


Introduction
============

This module implements the word2vec family of algorithms, using highly optimized C routines,
data streaming and Pythonic interfaces.

The word2vec algorithms include skip-gram and CBOW models, using either
hierarchical softmax or negative sampling: `Tomas Mikolov et al: Efficient Estimation of Word Representations
in Vector Space <https://arxiv.org/pdf/1301.3781.pdf>`_, `Tomas Mikolov et al: Distributed Representations of Words
and Phrases and their Compositionality <https://arxiv.org/abs/1310.4546>`_.

Other embeddings
================

There are more ways to train word vectors in Gensim than just Word2Vec.
See also :class:`~gensim.models.doc2vec.Doc2Vec`, :class:`~gensim.models.fasttext.FastText`.

The training algorithms were originally ported from the C package https://code.google.com/p/word2vec/
and extended with additional functionality and
`optimizations <https://rare-technologies.com/parallelizing-word2vec-in-python/>`_ over the years.

For a tutorial on Gensim word2vec, with an interactive web app trained on GoogleNews,
visit https://rare-technologies.com/word2vec-tutorial/.

Usage examples
==============

Initialize a model with e.g.:

.. sourcecode:: pycon

    >>> from gensim.test.utils import common_texts
    >>> from gensim.models import Word2Vec
    >>>
    >>> model = Word2Vec(sentences=common_texts, vector_size=100, window=5, min_count=1, workers=4)
    >>> model.save("word2vec.model")


**The training is streamed, so ``sentences`` can be an iterable**, reading input data
from the disk or network on-the-fly, without loading your entire corpus into RAM.

Note the ``sentences`` iterable must be *restartable* (not just a generator), to allow the algorithm
to stream over your dataset multiple times. For some examples of streamed iterables,
see :class:`~gensim.models.word2vec.BrownCorpus`,
:class:`~gensim.models.word2vec.Text8Corpus` or :class:`~gensim.models.word2vec.LineSentence`.

If you save the model you can continue training it later:

.. sourcecode:: pycon

    >>> model = Word2Vec.load("word2vec.model")
    >>> model.train([["hello", "world"]], total_examples=1, epochs=1)
    (0, 2)

The trained word vectors are stored in a :class:`~gensim.models.keyedvectors.KeyedVectors` instance, as `model.wv`:

.. sourcecode:: pycon

    >>> vector = model.wv['computer']  # get numpy vector of a word
    >>> sims = model.wv.most_similar('computer', topn=10)  # get other similar words

The reason for separating the trained vectors into `KeyedVectors` is that if you don't
need the full model state any more (don't need to continue training), its state can be discarded,
keeping just the vectors and their keys proper.

This results in a much smaller and faster object that can be mmapped for lightning
fast loading and sharing the vectors in RAM between processes:

.. sourcecode:: pycon

    >>> from gensim.models import KeyedVectors
    >>>
    >>> # Store just the words + their trained embeddings.
    >>> word_vectors = model.wv
    >>> word_vectors.save("word2vec.wordvectors")
    >>>
    >>> # Load back with memory-mapping = read-only, shared across processes.
    >>> wv = KeyedVectors.load("word2vec.wordvectors", mmap='r')
    >>>
    >>> vector = wv['computer']  # Get numpy vector of a word

Gensim can also load word vectors in the "word2vec C format", as a
:class:`~gensim.models.keyedvectors.KeyedVectors` instance:

.. sourcecode:: pycon

    >>> from gensim.test.utils import datapath
    >>>
    >>> # Load a word2vec model stored in the C *text* format.
    >>> wv_from_text = KeyedVectors.load_word2vec_format(datapath('word2vec_pre_kv_c'), binary=False)
    >>> # Load a word2vec model stored in the C *binary* format.
    >>> wv_from_bin = KeyedVectors.load_word2vec_format(datapath("euclidean_vectors.bin"), binary=True)

It is impossible to continue training the vectors loaded from the C format because the hidden weights,
vocabulary frequencies and the binary tree are missing. To continue training, you'll need the
full :class:`~gensim.models.word2vec.Word2Vec` object state, as stored by :meth:`~gensim.models.word2vec.Word2Vec.save`,
not just the :class:`~gensim.models.keyedvectors.KeyedVectors`.

You can perform various NLP tasks with a trained model. Some of the operations
are already built-in - see :mod:`gensim.models.keyedvectors`.

If you're finished training a model (i.e. no more updates, only querying),
you can switch to the :class:`~gensim.models.keyedvectors.KeyedVectors` instance:

.. sourcecode:: pycon

    >>> word_vectors = model.wv
    >>> del model

to trim unneeded model state = use much less RAM and allow fast loading and memory sharing (mmap).

Embeddings with multiword ngrams
================================

There is a :mod:`gensim.models.phrases` module which lets you automatically
detect phrases longer than one word, using collocation statistics.
Using phrases, you can learn a word2vec model where "words" are actually multiword expressions,
such as `new_york_times` or `financial_crisis`:

.. sourcecode:: pycon

    >>> from gensim.models import Phrases
    >>>
    >>> # Train a bigram detector.
    >>> bigram_transformer = Phrases(common_texts)
    >>>
    >>> # Apply the trained MWE detector to a corpus, using the result to train a Word2vec model.
    >>> model = Word2Vec(bigram_transformer[common_texts], min_count=1)

Pretrained models
=================

Gensim comes with several already pre-trained models, in the
`Gensim-data repository <https://github.com/RaRe-Technologies/gensim-data>`_:

.. sourcecode:: pycon

    >>> import gensim.downloader
    >>> # Show all available models in gensim-data
    >>> print(list(gensim.downloader.info()['models'].keys()))
    ['fasttext-wiki-news-subwords-300',
     'conceptnet-numberbatch-17-06-300',
     'word2vec-ruscorpora-300',
     'word2vec-google-news-300',
     'glove-wiki-gigaword-50',
     'glove-wiki-gigaword-100',
     'glove-wiki-gigaword-200',
     'glove-wiki-gigaword-300',
     'glove-twitter-25',
     'glove-twitter-50',
     'glove-twitter-100',
     'glove-twitter-200',
     '__testing_word2vec-matrix-synopsis']
    >>>
    >>> # Download the "glove-twitter-25" embeddings
    >>> glove_vectors = gensim.downloader.load('glove-twitter-25')
    >>>
    >>> # Use the downloaded vectors as usual:
    >>> glove_vectors.most_similar('twitter')
    [('facebook', 0.948005199432373),
     ('tweet', 0.9403423070907593),
     ('fb', 0.9342358708381653),
     ('instagram', 0.9104824066162109),
     ('chat', 0.8964964747428894),
     ('hashtag', 0.8885937333106995),
     ('tweets', 0.8878158330917358),
     ('tl', 0.8778461217880249),
     ('link', 0.8778210878372192),
     ('internet', 0.8753897547721863)]
