from google.cloud import storage
import os


def upload_folder_to_gcs(bucket_name, folder_path):
    # Create a client
    client = storage.Client()

    # Get the bucket
    bucket = client.get_bucket(bucket_name)

    # Iterate over the files in the folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Get the local file path
            local_file_path = os.path.join(root, file)

            # replace \ with / (windows -> unix)
            local_file_path = local_file_path.replace("\\", "/")

            # Create a blob object
            blob = bucket.blob("modelling/" + local_file_path)

            # Upload the file to GCS
            blob.upload_from_filename(local_file_path)

            print(f"Uploaded {local_file_path} to modelling/{local_file_path}")



def upload_file_to_gcs(bucket_name, local_file_path):
    # Create a client
    client = storage.Client()

    # Get the bucket
    bucket = client.get_bucket(bucket_name)

    # replace \ with / (windows -> unix)
    local_file_path = local_file_path.replace("\\", "/")

    # Create a blob object
    blob = bucket.blob("modelling/" + local_file_path)

    # Upload the file to GCS
    blob.upload_from_filename(local_file_path)

    print(f"Uploaded {local_file_path} to modelling/{local_file_path}")


# Usage example
bucket_name = "clickbait-detector-bucket"
folder_paths = [
    "clickbait_dataset", 
    "clickbait_dataset_more_variables", 
    "fake_news", 
    ]

file_paths = [
    "model_testing\\vertex_results.csv"
]


for folder_path in folder_paths:
    upload_folder_to_gcs(bucket_name, folder_path)

for file_path in file_paths:
    upload_file_to_gcs(bucket_name, file_path)
