"""Vertex AI connection module."""
import threading
from typing import Optional
from enum import Enum
from dataclasses import asdict


from news.vertex.configs.config import load_config_from_file
from vertexai.language_models import TextGenerationModel
from vertexai.preview import generative_models as gen
from google.auth import default, load_credentials_from_dict
from google.cloud import aiplatform


class ModelName(Enum):
    """Vertex AI model garden model names.

    See https://cloud.google.com/vertex-ai/docs/start/explore-models
    for more information.
    """
    BISON_001 = "text-bison@001"
    UNICORN_001 = "text-unicorn@001"
    BISON = "text-bison"
    BISON_32 = "text-bison-32k"
    GEMINI = "gemini-pro"


TITLE_PLACEHOLDER = "PLACE_FOR_TITLE"
SUMMARY_PLACEHOLDER = "PLACE_FOR_SUMMARY"


class VertexAI:  # pylint: disable=too-many-instance-attributes
    """Vertex AI class."""
    __slots__ = [
        "project_id",
        "location",
        "experiment",
        "staging_bucket",
        "credentials",
        "encryption_spec_key_name",
        "service_account",
        "my_chat_model",
        "model_name",
        "title",
        "prompt",
        "safety",
    ]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        experiment: Optional[str] = None,
        staging_bucket: Optional[str] = None,
        credentials=None,
        encryption_spec_key_name: Optional[str] = None,
        service_account: Optional[str] = None,
        model_name: ModelName = ModelName.GEMINI,
        title: str = "This is the Most Clickbait Title Ever!",
        prompt: str = "Is this title a clickbait: 'PLACE_FOR_TITLE'? Summary of the article: "
        "'PLACE_FOR_SUMMARY'. Return 1 if yes, 0 if no.",
        safety: bool = False,
    ):
        self.my_chat_model = None
        self.project_id = project_id
        self.location = location
        self.experiment = experiment
        self.staging_bucket = staging_bucket
        self.credentials = credentials
        self.encryption_spec_key_name = encryption_spec_key_name
        self.service_account = service_account
        self.model_name = model_name
        self.title = title
        self.prompt = prompt
        if not safety:
            self.safety = {
                gen.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: gen.HarmBlockThreshold.BLOCK_NONE,
                gen.HarmCategory.HARM_CATEGORY_HARASSMENT: gen.HarmBlockThreshold.BLOCK_NONE,
                gen.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: gen.HarmBlockThreshold.BLOCK_NONE,
                gen.HarmCategory.HARM_CATEGORY_HATE_SPEECH: gen.HarmBlockThreshold.BLOCK_NONE,
            }
        else:
            self.safety = {
                gen.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: gen.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # pylint: disable=line-too-long
                gen.HarmCategory.HARM_CATEGORY_HARASSMENT: gen.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # pylint: disable=line-too-long
                gen.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: gen.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # pylint: disable=line-too-long
                gen.HarmCategory.HARM_CATEGORY_HATE_SPEECH: gen.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # pylint: disable=line-too-long
            }
        self.init_connection()

    def init_connection(self):
        """Initialize Vertex AI connection."""
        aiplatform.init(
            project=self.project_id,
            location=self.location,
            experiment=self.experiment,
            staging_bucket=self.staging_bucket,
            credentials=self.credentials,
            encryption_spec_key_name=self.encryption_spec_key_name,
            service_account=self.service_account,
        )

    def load_config(self):
        """Load Vertex AI configuration."""
        try:
            self.credentials, self.project_id = load_credentials_from_dict(
                asdict(load_config_from_file())
            )
        except (FileNotFoundError, KeyError):
            self.credentials, self.project_id = default()

    def load_model(self):
        """Load Vertex AI model."""
        if self.model_name == ModelName.GEMINI:
            self.my_chat_model = gen.GenerativeModel(self.model_name.value)
            return
        self.my_chat_model = TextGenerationModel.from_pretrained(self.model_name.value)

    def predict(self):
        """Predict the clickbait score."""
        if self.model_name == ModelName.GEMINI:
            return self.predict_gemini()
        return self.my_chat_model.predict(self.prompt).text

    def predict_gemini(self):
        """Predict the clickbait score using Gemini."""
        return self.my_chat_model.generate_content(
            self.prompt,
            generation_config={"temperature": 0.3},
            safety_settings=self.safety,
        ).text

    def run(self, title, summary=None):
        """Run the model."""
        if summary:
            self.title = title
            self.prompt = (f"Is this title a clickbait: '{title}'?"
                           f"Summary of the article: '{summary}'. Return 1 if yes, 0 if no.")
        else:
            self.title = title
            self.prompt = (
                f"Is this title a clickbait: '{title}'? Return 1 if yes, 0 if no."
            )
        self.load_config()
        self.load_model()
        prediction = self.predict()
        return_value = prediction.strip() != "0"
        return return_value


def runner(vertex_ai: VertexAI, title: str):
    """Run the model in a thread."""
    vertex_ai.run(title=title)


def main():
    """Main function."""
    titles = [
        "You have to see this!",
        "Presidential election results",
        "Barack Obama claimed to be a lizard person",
        "EU to ban all cars by 2035",
        "Lionel Messi to join PSG",
    ]
    for title in titles:
        vertex_ai = VertexAI()
        t = threading.Thread(target=runner, args=(vertex_ai, title))
        t.start()


if "__main__" == __name__:
    main()
