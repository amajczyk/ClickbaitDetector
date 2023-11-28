from gensim.models import Word2Vec

class Word2VecModel():
    def __init__(self, model_settings) -> None:
        self.model = Word2Vec.load(model_settings['model_path'])
        self.model_settings = model_settings
        self.vector_size = self.model_settings['vector_size']
        self.is_skipgram = self.model_settings['is_skipgram']
        self.window_size = self.model_settings['window_size']
        self.vector_size = self.model_settings['vector_size']
    