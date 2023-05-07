import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm_notebook as tqdm
import numpy as np
import os
import sys
from tqdm import tqdm
from tabulate import tabulate
import glob
from IPython.display import display, HTML
import multiprocessing as mp

from gensim.models.word2vec import Word2Vec, LineSentence
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from mpl_toolkits.mplot3d import Axes3D
from sklearn.metrics import pairwise_distances

pd.options.display.max_rows = 20
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 200)
sns.set_style("whitegrid")

DATA_PATH = os.path.join(os.getcwd(), 'data', 'shwapno')
LOGGING_ENABLED = False
# TRAIN_ITEM_MODEL = True  # True - create and train a new model, False - load a previously created model
MODEL_DIR = './models'


# Helper functions
def to_readable(v):
    value = round(v, 2) if isinstance(v, float) else v
    if value < 1000:
        return str(value)
    elif value < 1000000:
        return str(round(value / 1000, 1)) + 'K'
    elif value >= 1000000:
        return str(round(value / 1000000, 1)) + 'M'
    return value


# def load_data(path=DATA_PATH):
#     if sys.platform == 'linux':
#         path_sep = '/'
#     elif sys.platform[:3] == 'win':
#         path_sep = '\\'
#     else:
#         path_sep = '/'
#
#     files_list = glob.glob(f'{path}/*.csv')
#     data_dict = {}
#     for file in files_list:
#         data = pd.read_csv(file)
#         data_dict[file.split(path_sep)[-1].split('.')[0]] = data
#     return data_dict, list(data_dict.keys())


# def get_basket_corpus(invoice_details):
#     invoice_details.ProductCode = invoice_details.ProductCode.astype(str)
#
#     product_codes_in_baskets = \
#         invoice_details.loc[invoice_details.index.repeat(invoice_details['SalesQTY'])].groupby('Invoiceno')[
#             'ProductCode'].apply(list)
#     product_names_in_basket = \
#         invoice_details.loc[invoice_details.index.repeat(invoice_details['SalesQTY'])].groupby('Invoiceno')[
#             'ProductName'].apply(list)
#     product_count = invoice_details.groupby('Invoiceno').ProductCode.apply(len).rename('ProductCount')
#     other_elements = invoice_details[
#         ['Invoiceno', 'CustomerCode', 'PrepareDate', 'WeekEndFlag', 'DayTimeFlag']].drop_duplicates().set_index(
#         'Invoiceno')
#     other_elements['PrepareDate'] = pd.to_datetime(other_elements.PrepareDate)
#
#     basket_corpus = pd.concat([product_codes_in_baskets, product_names_in_basket, product_count, other_elements],
#                               axis=1)
#     daytime_dict = {key: i for i, key in enumerate(basket_corpus.DayTimeFlag.unique())}
#     basket_corpus.DayTimeFlag = basket_corpus.DayTimeFlag.map(daytime_dict)
#
#     return basket_corpus


# def code2name(invoice_details, id):
#     product_code2name = \
#         invoice_details[['ProductCode', 'ProductName']].drop_duplicates().set_index('ProductCode').to_dict()[
#             'ProductName']
#     return product_code2name[id]
#
#
# def most_similar_readable(model, product_id, topn=10):
#     similar_list = [(product_id, 1.0)] + model.wv.most_similar(str(product_id), topn=topn)
#     return pd.DataFrame([(code2name(int(id)), str(id), similarity) for (id, similarity) in similar_list],
#                         columns=['product', 'ProductCode', 'similarity'])


class Item2Vec(Word2Vec):
    def __init__(self,
                 data_path=os.path.join(os.getcwd(), 'data', 'shwapno'),
                 window=5,
                 vector_size=100,
                 workers=3,
                 min_count=20,
                 epochs=20,
                 trim_rule=None,
                 callbacks=(),
                 **kwargs):
        self.data, data_keys = self.load_data(data_path)
        # get_stats(data['invoice_details'], True)
        if 'invoice_details' in self.data.keys():
            self.invoice = self.get_basket_corpus()
        else:
            raise KeyError(f"The data imported from {data_path} does not have the key 'invoice_details'. ")
        self.corpus_iterable = self.invoice.ProductCode.to_list()
        self.epochs = epochs
        super(Item2Vec, self).__init__(
            vector_size=vector_size,
            window=window,
            epochs=epochs,
            workers=workers,
            min_count=min_count,
            **kwargs
        )
        self._check_corpus_sanity(corpus_iterable=self.corpus_iterable, passes=(self.epochs + 1))
        self.build_vocab(corpus_iterable=self.corpus_iterable,
                         trim_rule=trim_rule)

    def load_data(self, path):
        if sys.platform == 'linux':
            path_sep = '/'
        elif sys.platform[:3] == 'win':
            path_sep = '\\'
        else:
            path_sep = '/'

        files_list = glob.glob(f'{path}/*.csv')
        data_dict = {}
        for file in files_list:
            data = pd.read_csv(file)
            data_dict[file.split(path_sep)[-1].split('.')[0]] = data
        return data_dict, list(data_dict.keys())

    def show_stats(self):
        stats = dict()
        stats['total_user'] = len(self.data['invoice_details'].CustomerCode.unique())
        stats['total_order'] = len(self.data['invoice_details'].Invoiceno.unique())
        stats['total_ordered_product'] = len(self.data['invoice_details'])
        stats['unique_products'] = len(self.data['invoice_details'].ProductCode.unique())
        print("total user = {}".format(to_readable(stats['total_user'])))
        print("total order = {} ({} orders per user)".format(to_readable(stats['total_order']),
                                                             to_readable(
                                                                 stats['total_order'] / stats['total_user'])))
        print("total product = ", to_readable(stats['unique_products']))
        print("total ordered product  = {} ({} orders per product)".format(
            to_readable(stats['total_ordered_product']),
            to_readable(
                stats['total_ordered_product'] / stats[
                    'unique_products'])))

        return stats

    def get_basket_corpus(self):
        self.data['invoice_details'].ProductCode = self.data['invoice_details'].ProductCode.astype(str)

        product_codes_in_baskets = \
            self.data['invoice_details'].loc[
                self.data['invoice_details'].index.repeat(self.data['invoice_details']['SalesQTY'])].groupby(
                'Invoiceno')[
                'ProductCode'].apply(list)
        product_names_in_basket = \
            self.data['invoice_details'].loc[
                self.data['invoice_details'].index.repeat(self.data['invoice_details']['SalesQTY'])].groupby(
                'Invoiceno')[
                'ProductName'].apply(list)
        product_count = self.data['invoice_details'].groupby('Invoiceno').ProductCode.apply(len).rename('ProductCount')
        other_elements = self.data['invoice_details'][
            ['Invoiceno', 'CustomerCode', 'PrepareDate', 'WeekEndFlag', 'DayTimeFlag']].drop_duplicates().set_index(
            'Invoiceno')
        other_elements['PrepareDate'] = pd.to_datetime(other_elements.PrepareDate)

        basket_corpus = pd.concat([product_codes_in_baskets, product_names_in_basket, product_count, other_elements],
                                  axis=1)
        daytime_dict = {key: i for i, key in enumerate(basket_corpus.DayTimeFlag.unique())}
        basket_corpus.DayTimeFlag = basket_corpus.DayTimeFlag.map(daytime_dict)

        return basket_corpus

    def code2name(self, id):
        product_code2name = \
            self.data['invoice_details'][['ProductCode', 'ProductName']].drop_duplicates().set_index('ProductCode').to_dict()[
                'ProductName']
        return product_code2name[id]

    def most_similar_readable(self, product_id, topn=10):
        similar_list = [(product_id, 1.0)] + self.wv.most_similar(str(product_id), topn=topn)
        return pd.DataFrame([(self.code2name(str(id)), str(id), similarity) for (id, similarity) in similar_list],
                            columns=['product', 'ProductCode', 'similarity'])

    def train(self):
        super(Item2Vec, self).train(corpus_iterable=self.corpus_iterable, total_examples=self.corpus_count,
                                    total_words=self.corpus_total_words, epochs=self.epochs, start_alpha=self.alpha,
                                    end_alpha=self.min_alpha, compute_loss=self.compute_loss)
