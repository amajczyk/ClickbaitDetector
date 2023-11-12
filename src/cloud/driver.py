# Driver code to manage requests and responses from Vertex AI model using code from connections.py

from src.cloud.connections import VertexAIModel, check_response
from src.configs.config import ENDPOINT_ID

# Create Vertex AI model object
model = VertexAIModel(region='us-central1', endpoint_id='1234567890')
