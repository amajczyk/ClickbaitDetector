from typing import Optional

from google.auth import default
from vertexai.language_models import TextGenerationModel


def init_sample(
        project: Optional[str] = None,
        location: Optional[str] = None,
        experiment: Optional[str] = None,
        staging_bucket: Optional[str] = None,
        credentials=None,
        encryption_spec_key_name: Optional[str] = None,
        service_account: Optional[str] = None,
):
    from google.cloud import aiplatform
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
    credentials, project_id = default()
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
