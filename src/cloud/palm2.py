import requests
from google.cloud import aiplatform

client = aiplatform.gapic.PredictionServiceClient(
    client_options=dict(
        api_endpoint="https://ai-platform.googleapis.com/v1/projects/<project-id>/locations/<location>/endpoints"
                     "/<endpoint-id>")
)

endpoint = "https://ai-platform.googleapis.com/v1/projects/<project-id>/locations/<location>/endpoints/<endpoint-id>"

request_body = {
    "text": "This is the Most Clickbait Title Ever!"
}

response = requests.post(endpoint, json=request_body)

if response.status_code == 200:
    response_body = response.json()
    prediction = response_body["predictions"][0]

    print("Predicted label:", prediction["label"])
