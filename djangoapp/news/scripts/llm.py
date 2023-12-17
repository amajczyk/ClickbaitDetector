from transformers import AutoTokenizer, AutoTokenizer, AutoModelForSequenceClassification, pipeline
import json

class LocalLLM:
    def __init__(self) -> None:

        # self.model_config_json = json.load(open("config.json"))
        model = 'christinacdl/clickbait_binary_detection'
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForSequenceClassification.from_pretrained(model)

    def predict(self, text):
    
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        predicted_class = outputs.logits.argmax().item()


        return predicted_class
    


