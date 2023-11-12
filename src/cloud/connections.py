# Write a set of functions which enable the user to connect to the GCP cloud platform and Vertex AI tool inside
# the cloud platform. The functions will be used to send an API request with text to LLM model deployed on Vertex AI
# and receive the response from the model.

# Import libraries
import google.auth
from google.cloud.aiplatform.gapic import prediction_service_client
from google.protobuf.struct_pb2 import Value
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import ParseDict


def get_credentials():
    """
    Function to get the credentials for the Vertex AI model.
    """
    credentials, project_id = google.auth.default()
    return credentials, project_id


def check_response(response):
    """
    Function to check if the response from the Vertex AI model contains boolean 'yes' or 'no' values.
    Contains, not equals.
    """
    if 'yes' in response:
        return True
    elif 'no' in response:
        return False
    else:
        return ValueError('Response does not contain boolean values.')


class VertexAIModel:

    text_base = "Is this title a clickbait: '"

    def __init__(self, region, endpoint_id):
        self.region = region
        self.endpoint_id = endpoint_id
        self.credentials, self.project_id = get_credentials()

    def get_prediction_endpoint(self):
        """
        Function to get the prediction endpoint for the Vertex AI model.
        """
        endpoint = f"projects/{self.project_id}/locations/{self.region}/endpoints/{self.endpoint_id}"
        return endpoint

    def get_prediction_client(self):
        """
        Function to get the prediction client for the Vertex AI model.
        """
        prediction_client = prediction_service_client.PredictionServiceClient(
            client_options={
                "api_endpoint": f"{self.region}-aiplatform.googleapis.com"
            }
        )
        return prediction_client

    def create_prediction_request(self, text):
        """
        Function to send the prediction request to the Vertex AI model.
        """
        prediction_request = Value(
            struct_value=Struct(
                fields={
                    f"{self.text_base}{text}'?": Value(string_value=text)
                }
            )
        )
        return prediction_request

    def call_model(self, text):
        """
        Function to send the text to the Vertex AI model.
        """
        endpoint = self.get_prediction_endpoint()
        prediction_client = self.get_prediction_client()
        prediction_request = self.create_prediction_request(text)
        response = prediction_client.predict(endpoint=endpoint, instances=[prediction_request])
        message_json = MessageToJson(response)
        return ParseDict(response, Value())[0].string_value, message_json
