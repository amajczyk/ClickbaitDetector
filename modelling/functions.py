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
from nltk.corpus import words
import inflect
import re 
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import copy as cp
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
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

def remove_possesive_s(text):
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




def replace_short_version(text):
    for p in all_quoatation:
        text = text.replace(p+'re', ' are')
        text = text.replace(p+'ve', ' have')
        text = text.replace(p+'ll', ' will')
        text = text.replace(p+'m', ' am')
        text = text.replace(p+'d', ' would')
        text = text.replace('n'+p+'t', ' not')
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


stop_words = set(stopwords.words('english'))

def tokenize(text):
    return [word for word in word_tokenize(text.lower()) if word not in stop_words]




def remove_non_ascii_characters_from_text(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])

def remove_non_ascii_characters_from_list(text_list):
    return [remove_non_ascii_characters_from_text(text) for text in text_list]



def remove_non_eng_words(text_list, words = words):
    return [word for word in text_list if word.lower() in words]
    


def preprocess_title(df):

    # df = cp.deepcopy(df)
    english_words = set(w.lower() for w in words.words())

    # remove punctuation and other stuff
    print("Replacing numbers with words...")
    df['title'] = df['title'].apply(replace_numbers_with_words)
    
    # remove possesive s
    print("Removing possesive s...")
    df['title'] = df['title'].apply(remove_possessive_nltk)

    # replace short versions
    print("Expanding short versions...")
    df['title'] = df['title'].apply(expand_contractions_nltk)

    # remove punctuation
    print("Removing punctuation...")
    df['title'] = df['title'].apply(remove_punct)

    # tokenize
    print("Tokenizing...")
    df['title'] = df['title'].apply(tokenize)
    # print(df['title'])
    
    # remove words in words_to_remove.txt
    print("Removing words in words_to_remove.txt...")
    df['title'] = df['title'].apply(lambda x: remove_words_from_file(x, 'words_to_remove.txt'))
    # print(df['title'])

    # stem words
    # print("Stemming words...")
    # df['title'] = df['title'].apply(lambda x: [get_stem_of_word(word) for word in x])

    # lemmalize words
    print("Lemmalizing words...")
    df['title'] = df['title'].apply(lambda x: [lemmalize_word(word) for word in x])

    # remove non ascii characters
    print("Removing non ascii characters...")
    df['title'] = df['title'].apply(remove_non_ascii_characters_from_list)

    # remove non english words
    print("Removing non english words...")
    df['title'] = df['title'].apply(remove_non_eng_words, words = english_words)

    # remove rows with empty titles
    print("Removing empty titles...")
    df = df[df['title'].apply(len) > 0]

    # remove stopwords one more time
    print("Removing stopwords one more time...")
    df['title'] = df['title'].apply(lambda x: [word for word in x if word not in stop_words])





    return df



####### MODEL FUNCTIONS ########
import pandas as pd
def predict_on_text(classifier, model_word2vec, text):
    # print(text)
    text = preprocess_title(pd.DataFrame({'title': [text]}))
    text = get_word_vectors(model_word2vec, text['title'][0], aggregation='mean')
    # print(len(text))
    return classifier.predict_proba(text.reshape(1, -1))