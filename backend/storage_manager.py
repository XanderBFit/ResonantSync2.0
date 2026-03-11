from google.cloud import storage

BUCKET_NAME = "resonant-crab-audio-storage-b4"
storage_client = storage.Client()

def upload_to_gcs(source_file_path: str, blob_name: str) -> bool:
    """Uploads a local file to the GCS bucket."""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(source_file_path)
        return True
    except Exception as e:
        print(f"GCS Upload Error: {e}")
        return False

def download_from_gcs(blob_name: str, dest_file_path: str) -> bool:
    """Downloads a file from the GCS bucket to a local path."""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return False
        blob.download_to_filename(dest_file_path)
        return True
    except Exception as e:
        print(f"GCS Download Error: {e}")
        return False

def find_blob_by_prefix(prefix: str) -> str:
    """Finds the first blob matching a given prefix."""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix=prefix))
        if blobs:
            return blobs[0].name
        return None
    except Exception as e:
        print(f"GCS Prefix Search Error: {e}")
        return None
