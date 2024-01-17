## model by christinacdl/clickbait_binary_detection from huggingface - https://huggingface.co/christinacdl/clickbait_binary_detection
## Under MIT License

from transformers import (
    AutoTokenizer,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline,
)
from torch.nn.functional import softmax


class LocalLLM:
    def __init__(self) -> None:
        model = "christinacdl/clickbait_binary_detection"
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForSequenceClassification.from_pretrained(model)
        self.proba_cutoff = 0.0043

    def predict(self, text:str) -> float:
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        probabilities = softmax(outputs.logits, dim=-1)
        return probabilities[0][1].item()
