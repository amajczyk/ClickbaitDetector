from google.cloud import storage

import os

bucket_name = "clickbait-detector-bucket"

# The ID of the folder to download
folder_paths = ["clickbait_dataset", "clickbait_dataset_more_variables", "fake_news", "model_testing"]


# The local path to download the folder to
local_path = ""
# os.makedirs(local_path, exist_ok=True)

storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)

for folder_path in folder_paths:
    blobs = bucket.list_blobs(prefix=str(os.path.join("modelling", folder_path)))
    

    for blob in blobs:
        # remove the last part of the path (the file name)
        dir = os.path.dirname(blob.name)
        dir = os.path.join(local_path, dir)
        print(dir)

        savepath = blob.name

        os.makedirs(dir, exist_ok=True)
        blob.download_to_filename(
            os.path.join(local_path, savepath)

        )

