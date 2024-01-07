import os
import pickle
from django.conf import settings
from news.scripts.scraping import Scraper
from transformers import pipeline
from news.scripts.nlp import NLP
from news.scripts.llm import LocalLLM
from news.vertex.cloud.vertex_connection import VertexAI

from nltk.corpus import wordnet


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class ModelLoader(metaclass=Singleton):
    def __init__(self):


        # load Scraper
        config_path = os.path.join(settings.BASE_DIR, 'news', 'config', 'site_variables_dict')
        self.scraper = Scraper(config_path)


        # load NLP model
        self.nlp = NLP() 

        # wordnet is lazy loaded, this poses a problem when using multiprocessing
        wordnet.ensure_loaded()


        # load LocalLLM
        self.llm = LocalLLM()

        # load summarizer
        self.summarizer = pipeline("summarization", model="Falconsai/text_summarization")
        
        # load VertexAI
        self.vertex = VertexAI()
        
