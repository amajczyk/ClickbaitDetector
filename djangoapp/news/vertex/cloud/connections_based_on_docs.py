import threading
from typing import Optional
from enum import Enum
from google.auth import default, load_credentials_from_dict
from news.vertex.configs.config import load_config_from_file
from vertexai.language_models import TextGenerationModel
from vertexai.preview.generative_models import GenerativeModel, Part
from dataclasses import asdict
from google.cloud import aiplatform


class ModelName(Enum):
    BISON_001 = "text-bison@001"
    UNICORN_001 = "text-unicorn@001"
    BISON = "text-bison"
    BISON_32 = "text-bison-32k"
    GEMINI = "gemini-pro"


TITLE_PLACEHOLDER = "PLACE_FOR_TITLE"
SUMMARY_PLACEHOLDER = "PLACE_FOR_SUMMARY"


class VertexAI:
    __slots__ = [
        'project_id',
        'location',
        'experiment',
        'staging_bucket',
        'credentials',
        'encryption_spec_key_name',
        'service_account',
        'my_chat_model',
        'model_name',
        'title',
        'prompt'
    ]

    def __init__(
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
            prompt: str = f"Is this title a clickbait: 'PLACE_FOR_TITLE'? Summary of the article: 'PLACE_FOR_SUMMARY'. Return 1 if yes, 0 if no."
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
        self.init_connection()

    def init_connection(self):
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
        try:
            self.credentials, self.project_id = load_credentials_from_dict(asdict(load_config_from_file()))
        except FileNotFoundError or KeyError:
            self.credentials, self.project_id = default()

    def load_model(self):
        if self.model_name == ModelName.GEMINI:
            self.my_chat_model = GenerativeModel(self.model_name.value)
            return
        self.my_chat_model = TextGenerationModel.from_pretrained(self.model_name.value)

    def predict(self, title: Optional[str] = None, summary: Optional[str] = None):
        if summary:
            self.prompt = self.prompt.replace(SUMMARY_PLACEHOLDER, summary)
        else:
            self.prompt = self.prompt.replace(SUMMARY_PLACEHOLDER, "No summary available.")
        if self.model_name == ModelName.GEMINI:
            return self.predict_gemini(title)
        if title:
            return self.my_chat_model.predict(self.prompt.replace(TITLE_PLACEHOLDER, title)).text
        return self.my_chat_model.predict(self.prompt.replace(TITLE_PLACEHOLDER, self.title)).text

    def predict_gemini(self, title: Optional[str] = None):
        if title:
            return self.my_chat_model.generate_content(
                self.prompt.replace(TITLE_PLACEHOLDER, title),
                generation_config={
                    "temperature": 0.3
                }
            ).text
        return self.my_chat_model.generate_content(
            self.prompt.replace(TITLE_PLACEHOLDER, self.title),
            generation_config={
                "temperature": 0.3
            }
        ).text

    def run(self, *args, **kwargs):
        self.prompt = kwargs.get('prompt', self.prompt)
        self.title = kwargs.get('title', self.title)
        summary = kwargs.get('summary', None)
        self.load_config()
        self.load_model()
        prediction = self.predict(summary=summary)
        print(f"Prediction: {prediction} for prompt: {self.prompt.replace(TITLE_PLACEHOLDER, self.title)}")
        return_value = False if prediction.strip() == '0' else True
        print(f"Return value: {return_value}")
        if summary:
            self.prompt = self.prompt.replace(summary, SUMMARY_PLACEHOLDER)
        else:
            self.prompt = self.prompt.replace("No summary available.", SUMMARY_PLACEHOLDER)
        print(f"Prompt after predicting (should be default): {self.prompt}")
        return return_value


def runner(
        vertex_ai: VertexAI,
        title: str,
        prompt: str = f"Is this title a clickbait: 'PLACE_FOR_TITLE'? Return 1 if yes, 0 if no."
):
    vertex_ai.run(
        title=title,
        prompt=prompt
    )


def main():
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
