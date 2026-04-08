import time
import io
import sys
import os
from unittest.mock import MagicMock

# Mock google auth and clients before anything else
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.cloud.storage'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Mock other heavy dependencies that might not be present
sys.modules['librosa'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['ffmpeg'] = MagicMock()
sys.modules['mutagen'] = MagicMock()
sys.modules['mutagen.mp3'] = MagicMock()
sys.modules['mutagen.id3'] = MagicMock()

import main
from main import app, verify_token, get_tags

# Mock Firestore
mock_db = MagicMock()
main.db = mock_db

# Mock download_from_gcs to simulate a slow download
def mock_download_from_gcs(blob_name, local_path):
    time.sleep(1.0) # Simulate 1 second download
    return True

# Mock read_disco_metadata
def mock_read_disco_metadata(local_path):
    return {"TIT2": "Test Title", "TPE1": "Test Artist"}

main.download_from_gcs = mock_download_from_gcs
main.read_disco_metadata = mock_read_disco_metadata

def run_benchmark():
    print("Running baseline benchmark for get_tags(file_id)...")

    file_id = "test-file-id"

    # We call the function directly as it's an async function
    # but since we're in a simple script without a running loop,
    # and it doesn't actually await much that needs a loop (other than being declared async),
    # we can use asyncio.run if we want to be proper.

    import asyncio

    async def call_get_tags():
        start = time.time()
        # Direct calls to the endpoint function
        tasks = [get_tags(file_id) for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        end = time.time()
        print(f"Total time for 5 requests: {end - start:.2f} seconds")
        for i, r in enumerate(responses):
            print(f"Request {i} result: {r}")

    asyncio.run(call_get_tags())

if __name__ == "__main__":
    run_benchmark()
