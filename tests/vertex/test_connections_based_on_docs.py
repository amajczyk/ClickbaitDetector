import pytest
from unittest.mock import patch, MagicMock
from src.cloud.connections_based_on_docs import VertexAI, ModelName
import google


@pytest.fixture
def vertex_ai():
    return VertexAI()


def test_init(vertex_ai):
    assert vertex_ai.project_id is None
    assert vertex_ai.location is None
    assert vertex_ai.experiment is None
    assert vertex_ai.staging_bucket is None
    assert vertex_ai.credentials is None
    assert vertex_ai.encryption_spec_key_name is None
    assert vertex_ai.service_account is None
    assert vertex_ai.model_name == ModelName.BISON_001
    assert vertex_ai.title == "This is the Most Clickbait Title Ever!"
    assert vertex_ai.prompt == "Is this title a clickbait: 'PLACE_FOR_TITLE'? Return 1 if yes, 0 if no."
    assert vertex_ai.my_chat_model is None


@patch('src.cloud.connections_based_on_docs.aiplatform.init')
def test_init_connection(mock_aiplatform_init, vertex_ai):
    vertex_ai.init_connection()
    mock_aiplatform_init.assert_called_once_with(
        project=vertex_ai.project_id,
        location=vertex_ai.location,
        experiment=vertex_ai.experiment,
        staging_bucket=vertex_ai.staging_bucket,
        credentials=vertex_ai.credentials,
        encryption_spec_key_name=vertex_ai.encryption_spec_key_name,
        service_account=vertex_ai.service_account,
    )


@patch('json.load')
def test_load_config(mock_json_load, vertex_ai):
    mock_json_load.return_value = {
        'refresh_token': 'fake_token',
        'project_id': 'fake_project_id',
        'type': 'authorized_user',
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret'
    }
    with patch('google.auth.load_credentials_from_dict') as mock_auth_load_credentials_from_dict:
        mock_auth_load_credentials_from_dict.return_value = (
            {"client_id": "fake_client_id", "client_secret": "fake_client_secret"},
            'fake_project_id'
        )
        vertex_ai.load_config()
    mock_json_load.assert_called_once()
    assert type(vertex_ai.credentials) == google.oauth2.credentials.Credentials
    assert vertex_ai.project_id == 'planar-courage-319110'


@patch('src.cloud.connections_based_on_docs.TextGenerationModel.from_pretrained')
def test_load_model(mock_from_pretrained, vertex_ai):
    vertex_ai.load_model()
    mock_from_pretrained.assert_called_once_with(vertex_ai.model_name.value)
    assert vertex_ai.my_chat_model is not None


@patch('vertexai.language_models.TextGenerationModel')
def test_predict(mock_predict, vertex_ai):
    mock_predict.return_value = MagicMock(predict=mock_predict.predict)
    mock_predict.predict.return_value = MagicMock(text='1')
    vertex_ai.my_chat_model = mock_predict
    result = vertex_ai.predict()
    assert result == '1'


def test_run(vertex_ai):
    with patch('src.cloud.connections_based_on_docs.VertexAI.predict') as mock_predict:
        mock_predict.return_value = '1'
        result = vertex_ai.run(title='My Clickbait Title')
    assert result is True


def test_run_not_clickbait(vertex_ai):
    with patch('src.cloud.connections_based_on_docs.VertexAI.predict') as mock_predict:
        mock_predict.return_value = '0'
        titles = [
            "A Comprehensive Review of the Latest Machine Learning Techniques",
            "The Impact of Artificial Intelligence on Society",
            "The Future of Work in the Age of Automation"
        ]
        for title in titles:
            result = vertex_ai.run(title=title)
            assert result is False
