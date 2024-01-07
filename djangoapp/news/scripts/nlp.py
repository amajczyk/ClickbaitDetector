import json
import numpy as np
from gensim.models import Word2Vec
import pickle
import os
import catboost
import pandas as pd
from django.conf import settings


class NLP():
    class Word2VecModel():
        def __init__(self) -> None:
            model_settings_path = os.path.join(settings.BASE_DIR, 'news', 'config', 'model_settings.json')
            self.model_settings = return_best_model(path=model_settings_path)
            
            w2v_path = os.path.join(settings.BASE_DIR, 'news', 'word2vec_models', self.model_settings['model_path'])
            self.model = Word2Vec.load(w2v_path)

            self.is_skipgram = self.model_settings['is_skipgram']
            self.window_size = self.model_settings['window_size']
            self.vector_size = self.model_settings['vector_size']

    class PredictiveModel():
        def __init__(self) -> None:
            model_path = os.path.join(settings.BASE_DIR, 'news', 'predictive_models', 'lightgbm.pkl')
            self.model = pickle.load(open(model_path, 'rb'))
        
    class Scaler():
        def __init__(self) -> None:
            scaler_path = os.path.join(settings.BASE_DIR, 'news', 'predictive_models', 'scaler.pkl')
            self.scaler = pickle.load(open(scaler_path, 'rb'))

    def __init__(self) -> None:
        w2v = self.Word2VecModel()
        predictive_model = self.PredictiveModel().model
        scaler = self.Scaler().scaler

        self.w2v = w2v
        self.predictive_model = predictive_model
        self.scaler = scaler
        self.proba_cutoff = 0.3490965225838074

    def predict_on_text(self, title):
        
        # print(text)
        text = preprocess_title(pd.DataFrame({'title': [title]}))
        text = get_word_vectors(self.w2v, text['title'][0], aggregation='mean')
        text = self.scaler.transform([text])
        # print(len(text))
        return self.predictive_model.predict_proba(text.reshape(1, -1))
            

def return_best_model(path: str):
    # Load the best model from the model_settings.json file (best_word2vec property)
    with open(path) as json_file:
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
    
def load_predictive_model(path:str):
    classifier = pickle.load(open(path, 'rb'))
    return classifier
    


####### PREPROCESSING FUNCTIONS ########
# remove punctuation
import string
from nltk.corpus import words as nltk_corpus_words
import inflect
import re 
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import copy as cp
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()




punct = string.punctuation
punct = punct
all_quoatation = ['“', '”', '‘', '’', '’', '‘', '’', '‘', u'\u2018', u'\u2019', u'\u201c', u'\u201d', u'\u2032', u'\u2033', '“',  '”',]


def get_stem_of_word(text):
    return stemmer.stem(text)

def lemmalize_word(text):
    return lemmatizer.lemmatize(text)


def remove_punct(text, punct=punct):
    for p in punct:
        text = text.replace(p, '')
    text = text.replace('...', ' ')
    text = text.replace('…', ' ')
    text = text.replace('—', ' ')
    text = text.replace('–', ' ')
    text = text.replace('–', ' ')
    text = text.replace( '—', ' ')

    translator = str.maketrans("", "", string.punctuation)
    text = text.translate(translator)

    return text

def remove_possessive(text):
    for p in all_quoatation:
        text = text.replace(p+'s', '')
        text = text.replace('s'+ p, '')
    return text

def remove_possessive_nltk(text):
    words_ = word_tokenize(text)
    tagged_words = pos_tag(words_)

    updated_words = []
    for i, (word, pos) in enumerate(tagged_words):
        if i > 0 and pos == 'POS' and tagged_words[i - 1][1] == 'NN':
            continue
        updated_words.append(word)

    result = ' '.join(updated_words)
    return result



def expand_contractions_nltk(text):
    words = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()

    expanded_words = []
    for word in words:
        # Use lemmatization to handle contractions
        expanded_word = lemmatizer.lemmatize(word)
        expanded_words.append(expanded_word)

    result = ' '.join(expanded_words)
    return result



import re

def replace_short_version(text):
    for p in all_quoatation:
        text = re.sub(r'\b' + p + 're\b', ' are', text)
        text = re.sub(r'\b' + p + 've\b', ' have', text)
        text = re.sub(r'\b' + p + 'll\b', ' will', text)
        text = re.sub(r'\b' + p + 'm\b', ' am', text)
        text = re.sub(r'\b' + p + 'd\b', ' would', text)
        text = re.sub(r'\b' + 'n' + p + 't\b', ' not', text)
    return text 

def remove_words_from_file(text_list, file_name):
    # print(text)
    with open(file_name) as f:
        words = f.readlines()
    words = [word.strip() for word in words]
    # print(words)
   
    text = [word for word in text_list if word not in words]

    return text   





def replace_numbers_with_words(text):
    regex = r'\b\d+\b'

    matched = re.finditer(regex, text)

    for m in matched:
        number = m.group()
        p = inflect.engine()
        text = text.replace(number, p.number_to_words(number))
    return text



def tokenize(text):
    stop_words = set(stopwords.words('english'))
    return [word for word in word_tokenize(text.lower()) if word not in stop_words]




def remove_non_ascii_characters_from_text(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])

def remove_non_ascii_characters_from_list(text_list):
    return [remove_non_ascii_characters_from_text(text) for text in text_list]



def remove_non_eng_words(text_list, words = nltk_corpus_words):
    return [word for word in text_list if word.lower() in words]
    


def preprocess_title(df, verbose = False):

    # df = cp.deepcopy(df)
    
    english_words = set(w.lower() for w in nltk_corpus_words.words())

    # remove punctuation and other stuff
    if verbose:
        print(df['title'])
        print("Removing numbers and replacing with words...")   
    df['title'] = df['title'].apply(replace_numbers_with_words)
    
    # remove possesive s
    if verbose:
        print(df['title'])
        print("Removing possesive s...")
    df['title'] = df['title'].apply(remove_possessive)

    # replace short versions
    if verbose:
        print(df['title'])
        print("Expanding short versions...")
    df['title'] = df['title'].apply(replace_short_version)

    # remove punctuation
    if verbose:
        print(df['title'])
        print("Removing punctuation...")   
    df['title'] = df['title'].apply(remove_punct)


    # replace US with USA
    if verbose:
        print(df['title'])
        print("Replacing US with USA...")
    df['title'] = df['title'].apply(lambda x: x.replace('US', 'USA'))

    # tokenize
    if verbose:
        print(df['title'])
        print("Tokenizing...")
        
    df['title'] = df['title'].apply(tokenize)
    # print(df['title'])
    
    # remove words in words_to_remove.txt
    # if verbose:
    #     print(df['title'])
    #     print("Removing words in words_to_remove.txt...")
    # df['title'] = df['title'].apply(lambda x: remove_words_from_file(x, 'words_to_remove.txt'))
    # print(df['title'])

    # stem words
    # print("Stemming words...")
    # df['title'] = df['title'].apply(lambda x: [get_stem_of_word(word) for word in x])

    
    # lemmalize words
    if verbose:
        print(df['title'])
        print("Lemmalizing words...")
    df['title'] = df['title'].apply(lambda x: [lemmalize_word(word) for word in x])

    # remove non ascii characters
    if verbose:
        print(df['title'])
        print("Removing non ascii characters...")
        
    df['title'] = df['title'].apply(remove_non_ascii_characters_from_list)

    # remove non english words
    # if verbose:
    #     print(df['title'])
    #     print("Removing non english words...")
    # df['title'] = df['title'].apply(remove_non_eng_words, words = english_words)

    # remove rows with empty titles
    if verbose:
        print(df['title'])
        print("Removing empty titles...")
        
    df = df[df['title'].apply(len) > 0]

    # remove stopwords one more time
    if verbose:
        print(df['title'])
        print("Removing stopwords one more time...")
    stop_words = set(stopwords.words('english'))
    df['title'] = df['title'].apply(lambda x: [word for word in x if word not in stop_words])





    return df



####### MODEL FUNCTIONS ########
import pandas as pd
