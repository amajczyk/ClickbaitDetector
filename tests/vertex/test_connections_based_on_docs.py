import os

import pytest
from unittest.mock import patch, MagicMock
from src.cloud.connections_based_on_docs import init_sample


@patch('src.cloud.connections_based_on_docs.aiplatform.init')
def test_init_sample(mock_init):
    # Arrange
    project = 'test_project'
    location = 'test_location'
    experiment = 'test_experiment'
    staging_bucket = 'test_bucket'
    credentials = 'test_credentials'
    encryption_spec_key_name = 'test_key_name'
    service_account = 'test_account'

    # Act
    init_sample(project, location, experiment, staging_bucket, credentials, encryption_spec_key_name, service_account)

    # Assert
    mock_init.assert_called_once_with(
        project=project,
        location=location,
        experiment=experiment,
        staging_bucket=staging_bucket,
        credentials=credentials,
        encryption_spec_key_name=encryption_spec_key_name,
        service_account=service_account,
    )


@patch('src.cloud.connections_based_on_docs.aiplatform.init')
@patch('src.cloud.connections_based_on_docs.TextGenerationModel.from_pretrained')
@patch('src.cloud.connections_based_on_docs.auth.load_credentials_from_dict')
@patch('src.cloud.connections_based_on_docs.config.load_config')
def test_main(mock_load_config, mock_load_credentials, mock_from_pretrained, mock_init):
    # Arrange
    mock_load_config.return_value = MagicMock(client_id='test_id', client_secret='test_secret')
    mock_load_credentials.return_value = ('test_credentials', 'test_project_id')
    mock_from_pretrained.return_value = MagicMock(predict=MagicMock(return_value=MagicMock(text='1')))
    mock_init.return_value = MagicMock()
    # Act
    with patch('src.cloud.connections_based_on_docs.__name__', "__main__"):
        with patch('src.cloud.connections_based_on_docs.print') as mock_print:
            import src.cloud.connections_based_on_docs as main
            main.main()

    # Assert
    mock_load_config.assert_called_once()
    mock_load_credentials.assert_called_once_with({
        "type": "authorized_user",
        "project_id": "planar-courage-319110",
        "refresh_token": "",
        "client_id": "test_id",
        "client_secret": "test_secret",
    })
    mock_init.assert_called_once_with(
        project='test_project_id',
        location=None,
        experiment="clickbait",
        staging_bucket="clickbait-detector-bucket",
        credentials=None,
        encryption_spec_key_name=None,
        service_account=None,
    )
    mock_from_pretrained.assert_called_once_with("text-bison@001")
    mock_print.assert_called()
