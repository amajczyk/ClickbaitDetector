"""NLP module for news app."""
import json
import os
import pickle
import re
import string

import numpy as np
from gensim.models import Word2Vec
import catboost
import pandas as pd
from django.conf import settings
from nltk.corpus import words as nltk_corpus_words
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tag import pos_tag
import inflect



def return_best_model(path: str):
    """Return the best model."""
    # Load the best model from the model_settings.json file (best_word2vec property)
    with open(path, "r", encoding="utf-8") as json_file:
        model_settings = json.load(json_file)
    return model_settings["best_word2vec"]


class NLP:  # pylint: disable=too-many-instance-attributes
    """NLP class."""
    def __init__(self) -> None:
        w2v = self.Word2VecModel()
        predictive_model = self.PredictiveModel().model
        scaler = self.Scaler().scaler

        self.w2v = w2v
        self.predictive_model = predictive_model
        self.scaler = scaler
        self.proba_cutoff = 0.38823882388238823
        self.dropped_dims = self.get_dimensions_to_drop()

        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()

        self.punct = string.punctuation
        self.all_quoatation = [
            "“",
            "”",
            "‘",
            "’",
            "’",
            "‘",
            "’",
            "‘",
            "\u2018",
            "\u2019",
            "\u201c",
            "\u201d",
            "\u2032",
            "\u2033",
            "“",
            "”",
        ]

    class Word2VecModel:  # pylint: disable=too-few-public-methods
        """Word2Vec model class."""
        def __init__(self) -> None:
            """Initialize the Word2Vec model."""
            model_settings_path = os.path.join(
                settings.BASE_DIR, "news", "config", "model_settings.json"
            )
            self.model_settings = return_best_model(path=model_settings_path)

            w2v_path = os.path.join(
                settings.BASE_DIR,
                "news",
                "word2vec_models",
                self.model_settings["model_path"],
            )

            self.model = Word2Vec.load(w2v_path)

            self.is_skipgram = self.model_settings["is_skipgram"]
            self.window_size = self.model_settings["window_size"]
            self.vector_size = self.model_settings["vector_size"]

    class PredictiveModel:  # pylint: disable=too-few-public-methods
        """Predictive model class."""
        def __init__(self) -> None:
            model_path = os.path.join(
                settings.BASE_DIR, "news", "predictive_models", "catboost.pkl"
            )
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)

    class Scaler:  # pylint: disable=too-few-public-methods
        """Scaler class."""
        def __init__(self) -> None:
            scaler_path = os.path.join(
                settings.BASE_DIR, "news", "predictive_models", "scaler.pkl"
            )
            with open(scaler_path, "rb") as f:
                self.scaler = pickle.load(f)

    def predict_on_text(self, title: str) -> np.ndarray:
        """Predict on text."""
        # print(text)
        text = self.preprocess_title(pd.DataFrame({"title": [title]}))
        text = self.get_word_vectors(self.w2v, text["title"][0], aggregation="mean")

        # drop dimensions
        text = np.delete(text, self.dropped_dims)

        text = self.scaler.transform([text])
        # print(len(text))
        return self.predictive_model.predict_proba(text.reshape(1, -1))

    def get_dimensions_to_drop(self) -> list:
        """Get dimensions to drop."""
        var_path = os.path.join(
            settings.BASE_DIR,
            "news",
            "predictive_models",
            "worst_performing_dimensions_intersection.pkl",
        )
        # read variables to be dropped from pickle file
        with open(var_path, "rb") as f:
            variables_to_drop = pickle.load(f)

        variables_to_drop = [x.replace("dim_", "") for x in variables_to_drop]
        variables_to_drop = [int(x) for x in variables_to_drop]
        return variables_to_drop

    def get_word_vectors(
        self, w2v_model: Word2VecModel, title: str, aggregation=None
    ) -> np.ndarray:
        """Get word vectors."""
        model = w2v_model.model
        word_vectors = [model.wv[word] for word in title if word in model.wv]
        # print(len(word_vectors))
        # print(word_vectors)
        if len(word_vectors) == 0:
            return np.zeros(model.vector_size)
        if aggregation == "mean":
            return np.mean(word_vectors, axis=0)
        if aggregation is None:
            return np.ndarray(word_vectors)
        return np.zeros(model.vector_size)

    def load_predictive_model(self, path: str) -> catboost.CatBoostClassifier:
        """Load predictive model."""
        with open(path, "rb") as f:
            classifier = pickle.load(f)
        return classifier

    def lemmalize_word(self, text: str) -> str:
        """Lemmalize word."""
        return self.lemmatizer.lemmatize(text)

    def remove_punct(self, text: str) -> str:
        """Remove punctuation."""
        for p in self.punct:
            text = text.replace(p, "")
        text = text.replace("...", " ")
        text = text.replace("…", " ")
        text = text.replace("—", " ")
        text = text.replace("–", " ")
        text = text.replace("–", " ")
        text = text.replace("—", " ")

        translator = str.maketrans("", "", string.punctuation)
        text = text.translate(translator)

        return text

    def remove_possessive(self, text: str) -> str:
        """Remove possessive."""
        for p in self.all_quoatation:
            text = text.replace(p + "s", "")
            text = text.replace("s" + p, "")
        return text

    def remove_possessive_nltk(self, text: str) -> str:
        """Remove possessive nltk."""
        words_ = word_tokenize(text)
        tagged_words = pos_tag(words_)

        updated_words = []
        for i, (word, pos) in enumerate(tagged_words):
            if i > 0 and pos == "POS" and tagged_words[i - 1][1] == "NN":
                continue
            updated_words.append(word)

        result = " ".join(updated_words)
        return result

    def expand_contractions_nltk(self, text: str) -> str:
        """Expand contractions nltk."""
        words = word_tokenize(text)
        lemmatizer = WordNetLemmatizer()

        expanded_words = []
        for word in words:
            # Use lemmatization to handle contractions
            expanded_word = lemmatizer.lemmatize(word)
            expanded_words.append(expanded_word)

        result = " ".join(expanded_words)
        return result

    def replace_short_version(self, text: string) -> string:
        """Replace short version."""
        for p in self.all_quoatation:
            text = re.sub(r"\b" + p + "re\b", " are", text)
            text = re.sub(r"\b" + p + "ve\b", " have", text)
            text = re.sub(r"\b" + p + "ll\b", " will", text)
            text = re.sub(r"\b" + p + "m\b", " am", text)
            text = re.sub(r"\b" + p + "d\b", " would", text)
            text = re.sub(r"\b" + "n" + p + "t\b", " not", text)
        return text

    def remove_words_from_file(self, text_list: list, file_name: str):
        """Remove words from file."""
        with open(file_name, "r", encoding="utf-8") as f:
            words = f.readlines()
        words = [word.strip() for word in words]

        text = [word for word in text_list if word not in words]

        return text

    def replace_numbers_with_words(self, text: list) -> str:
        """Replace numbers with words."""
        regex = r"\b\d+\b"

        matched = re.finditer(regex, text)

        for m in matched:
            number = m.group()
            p = inflect.engine()
            text = text.replace(number, p.number_to_words(number))
        return text

    def tokenize(self, text: list) -> list:
        """Tokenize."""
        stop_words = set(stopwords.words("english"))
        return [word for word in word_tokenize(text.lower()) if word not in stop_words]

    def remove_non_ascii_characters_from_text(self, text: list) -> str:
        """Remove non ascii characters from text."""
        return "".join([i if ord(i) < 128 else " " for i in text])

    def remove_non_ascii_characters_from_list(self, text_list: list) -> list:
        """Remove non ascii characters from list."""
        return [self.remove_non_ascii_characters_from_text(text) for text in text_list]

    def remove_non_eng_words(
        self, text_list: list, words: list = nltk_corpus_words
    ) -> list:
        """Remove non english words."""
        return [word for word in text_list if word.lower() in words]

    def preprocess_title(self, df: pd.DataFrame, verbose=False) -> pd.DataFrame:
        """Preprocess title."""
        # remove punctuation and other stuff
        if verbose:
            print(df["title"])
            print("Removing numbers and replacing with words...")
        df["title"] = df["title"].apply(self.replace_numbers_with_words)

        # remove possesive s
        if verbose:
            print(df["title"])
            print("Removing possesive s...")
        df["title"] = df["title"].apply(self.remove_possessive)

        # replace short versions
        if verbose:
            print(df["title"])
            print("Expanding short versions...")
        df["title"] = df["title"].apply(self.replace_short_version)

        # remove punctuation
        if verbose:
            print(df["title"])
            print("Removing punctuation...")
        df["title"] = df["title"].apply(self.remove_punct)

        # replace US with USA
        if verbose:
            print(df["title"])
            print("Replacing US with USA...")
        df["title"] = df["title"].apply(lambda x: x.replace("US", "USA"))

        # tokenize
        if verbose:
            print(df["title"])
            print("Tokenizing...")

        df["title"] = df["title"].apply(self.tokenize)

        # lemmalize words
        if verbose:
            print(df["title"])
            print("Lemmalizing words...")
        df["title"] = df["title"].apply(
            lambda x: [self.lemmalize_word(word) for word in x]
        )

        # remove non ascii characters
        if verbose:
            print(df["title"])
            print("Removing non ascii characters...")

        df["title"] = df["title"].apply(self.remove_non_ascii_characters_from_list)

        # remove non english words
        # if verbose:
        #     print(df['title'])
        #     print("Removing non english words...")
        # df['title'] = df['title'].apply(remove_non_eng_words, words = english_words)

        # remove rows with empty titles
        if verbose:
            print(df["title"])
            print("Removing empty titles...")

        df = df[df["title"].apply(len) > 0]

        # remove stopwords one more time
        if verbose:
            print(df["title"])
            print("Removing stopwords one more time...")
        stop_words = set(stopwords.words("english"))
        df["title"] = df["title"].apply(
            lambda x: [word for word in x if word not in stop_words]
        )

        # remove spaces
        df["title"] = df["title"].apply(lambda x: [word for word in x if word != " "])

        return df
