from transformers import AutoTokenizer, AutoTokenizer, AutoModelForSequenceClassification
import json

class LocalLLM:
    def __init__(self) -> None:

        self.model_config_json = json.load(open("config.json"))
        self.tokenizer = AutoTokenizer.from_pretrained("elozano/bert-base-cased-clickbait-news")
        self.model = AutoModelForSequenceClassification.from_pretrained("elozano/bert-base-cased-clickbait-news")

    def predict(self, text):
    
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        predicted_class = outputs.logits.argmax().item()


        return predicted_class
