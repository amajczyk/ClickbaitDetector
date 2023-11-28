import json
from typing import Optional

from google.auth import default
from src.configs import config
from vertexai.language_models import TextGenerationModel
from google.cloud import aiplatform
import google.auth as auth


def init_sample(
        project: Optional[str] = None,
        location: Optional[str] = None,
        experiment: Optional[str] = None,
        staging_bucket: Optional[str] = None,
        credentials=None,
        encryption_spec_key_name: Optional[str] = None,
        service_account: Optional[str] = None,
):
    aiplatform.init(
        project=project,
        location=location,
        experiment=experiment,
        staging_bucket=staging_bucket,
        credentials=credentials,
        encryption_spec_key_name=encryption_spec_key_name,
        service_account=service_account,
    )


if "__main__" == __name__:
    config = config.load_config()
    user_input_credentials = {
        "type": "authorized_user",
        "project_id": "planar-courage-319110",
        "refresh_token": f"{config['refresh_token']}",
        "client_id": f"{config['client_id']}",
        "client_secret": f"{config['client_secret']}",
    }
    credentials, project_id = auth.load_credentials_from_dict(user_input_credentials)
    init_sample(
        project_id,
        experiment="clickbait",
        staging_bucket="clickbait-detector-bucket",
        credentials=credentials,
    )
    my_chat_model = TextGenerationModel.from_pretrained("text-bison@001")
    prediction = my_chat_model.predict(
        "Is this title a clickbait: 'This is the Most Clickbait Title Ever!'? Return 1 if yes, 0 if no."
    )
    boolean_response = bool(prediction.text)
    print(prediction)
    print(boolean_response)