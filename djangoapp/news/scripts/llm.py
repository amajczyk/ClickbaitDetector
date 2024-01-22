""" model by
christinacdl/clickbait_binary_detection from huggingface -
https://huggingface.co/christinacdl/clickbait_binary_detection
Under MIT License
"""

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)
from torch.nn.functional import softmax


class LocalLLM:  # pylint: disable=too-few-public-methods
    """Local LLM class."""

    def __init__(self) -> None:
        model = "christinacdl/clickbait_binary_detection"
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForSequenceClassification.from_pretrained(model)
        self.proba_cutoff = 0.5

    def predict(self, text: str) -> float:
        """Predict."""
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        probabilities = softmax(outputs.logits, dim=-1)
        return probabilities[0][1].item()
