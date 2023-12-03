import threading
from typing import Optional
from enum import Enum
from google.auth import default, load_credentials_from_dict
from src.configs import config
from vertexai.language_models import TextGenerationModel
from dataclasses import asdict
from google.cloud import aiplatform


class ModelName(Enum):
    BISON_001 = "text-bison@001"
    UNICORN_001 = "text-unicorn@001"
    BISON = "text-bison"
    BISON_32 = "text-bison-32k"


TITLE_PLACEHOLDER = "PLACE_FOR_TITLE"


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
            model_name: ModelName = ModelName.BISON_001,
            title: str = "This is the Most Clickbait Title Ever!",
            prompt: str = f"Is this title a clickbait: 'PLACE_FOR_TITLE'? Return 1 if yes, 0 if no."
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
            self.credentials, self.project_id = load_credentials_from_dict(asdict(config.load_config()))
        except FileNotFoundError or KeyError:
            self.credentials, self.project_id = default()

    def load_model(self):
        self.my_chat_model = TextGenerationModel.from_pretrained(self.model_name.value)

    def predict(self, title: Optional[str] = None):
        if title:
            return self.my_chat_model.predict(self.prompt.replace(TITLE_PLACEHOLDER, title)).text
        return self.my_chat_model.predict(self.prompt.replace(TITLE_PLACEHOLDER, self.title)).text

    def run(self, *args, **kwargs):
        self.prompt = kwargs.get('prompt', self.prompt)
        self.title = kwargs.get('title', self.title)
        self.load_config()
        self.load_model()
        prediction = self.predict()
        print(f"Prediction: {prediction} for prompt: {self.prompt.replace(TITLE_PLACEHOLDER, self.title)}")
        return False if prediction == '0' else True


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
