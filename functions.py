import json
import numpy as np


def return_best_model():
    # Load the best model from the model_settings.json file (best_word2vec property)
    with open('model_settings.json') as json_file:
        model_settings = json.load(json_file)
    return model_settings['best_word2vec']

def get_word_vectors(w2v_model, title, aggregation=None):
    model = w2v_model.model
    word_vectors = [model.wv[word] for word in title if word in model.wv]
    # print(len(word_vectors))
    # print(word_vectors)
    if len(word_vectors) == 0:
        return np.zeros(model.vector_size)
    elif aggregation == 'mean':
        return np.mean(word_vectors, axis=0)
    elif aggregation is None:
        return word_vectors
    


####### PREPROCESSING FUNCTIONS ########
# remove punctuation
import string
punct = string.punctuation
punct = punct
all_quoatation = ['“', '”', '‘', '’', '’', '‘']

def remove_punct(text, punct=punct):
    for p in punct:
        text = text.replace(p, '')
    text = text.replace('...', ' ')
    text = text.replace('…', ' ')
    return text

def remove_possesive_s(text):
    for p in all_quoatation:
        text = text.replace(p+'s', '')
        text = text.replace('s'+ p, '')
    return text

def replace_short_version(text):
    for p in all_quoatation:
        text = text.replace(p+'re', ' are')
        text = text.replace(p+'ve', ' have')
        text = text.replace(p+'ll', ' will')
        text = text.replace(p+'m', ' am')
        text = text.replace(p+'d', ' would')
        text = text.replace('n'+p+'t', ' not')
    return text    



import inflect
import re 
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

def replace_numbers_with_words(text):
    regex = r'\b\d+\b'

    matched = re.finditer(regex, text)

    for m in matched:
        number = m.group()
        p = inflect.engine()
        text = text.replace(number, p.number_to_words(number))
    return text


stop_words = set(stopwords.words('english'))

def tokenize(text):
    return [word for word in word_tokenize(text.lower()) if word not in stop_words]

def preprocess_title(df):
    # remove punctuation and other stuff
    df['title'] = df['title'].apply(replace_numbers_with_words)
    df['title'] = df['title'].apply(remove_punct)
    df['title'] = df['title'].apply(remove_possesive_s)
    df['title'] = df['title'].apply(replace_short_version)

    # tokenize
    df['title'] = df['title'].apply(tokenize)
    return df



####### MODEL FUNCTIONS ########
import pandas as pd
def predict_on_text(classifier, model_word2vec, text):
    # print(text)
    text = preprocess_title(pd.DataFrame({'title': [text]}))
    text = get_word_vectors(model_word2vec, text['title'][0], aggregation='mean')
    # print(len(text))
    return classifier.predict_proba(text.reshape(1, -1))