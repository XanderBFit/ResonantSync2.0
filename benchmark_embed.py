import asyncio
import httpx
import time
import io
import sys
import os
import json

from unittest.mock import MagicMock

# Mock google auth before anything else
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.cloud.storage'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['librosa'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['ffmpeg'] = MagicMock()

# Add backend to sys.path so it can import its own modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

import main
from main import app, verify_token

# Mock dependencies
async def mock_verify_token():
    return "test-uid"

app.dependency_overrides[verify_token] = mock_verify_token

def mock_find_blob_by_prefix(prefix):
    return f"{prefix}.mp3"

def mock_download_from_gcs(blob_name, local_path):
    time.sleep(0.5) # Simulate blocking I/O
    # create a dummy file
    with open(local_path, "w") as f:
        f.write("dummy")
    return True

def mock_downmix_to_mp3(in_path, out_path):
    time.sleep(0.5) # Simulate blocking I/O
    with open(out_path, "w") as f:
        f.write("dummy")
    return True

def mock_embed_disco_metadata(local_mp3_path, data):
    time.sleep(0.5) # Simulate blocking I/O
    return True

def mock_generate_one_sheet(local_mp3_path, data, local_pdf_path):
    time.sleep(0.5) # Simulate blocking I/O
    with open(local_pdf_path, "w") as f:
        f.write("dummy")
    return True

def mock_upload_to_gcs(path, name):
    time.sleep(0.5) # Simulate blocking I/O
    return True

main.find_blob_by_prefix = mock_find_blob_by_prefix
main.download_from_gcs = mock_download_from_gcs
main.downmix_to_mp3 = mock_downmix_to_mp3
main.embed_disco_metadata = mock_embed_disco_metadata
main.generate_one_sheet = mock_generate_one_sheet
main.upload_to_gcs = mock_upload_to_gcs

async def run_benchmark():
    # Requires httpx.ASGITransport
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.time()

        # Send N requests concurrently
        N = 5
        tasks = []
        for _ in range(N):
            data = {
                'fileId': 'test_file_id',
                'metadata': json.dumps({'title': 'Test'}),
                'uid': 'test-uid'
            }
            tasks.append(client.post("/api/embed", data=data))

        responses = await asyncio.gather(*tasks)

        end = time.time()
        print(f"Total time for {N} requests: {end - start:.2f} seconds")
        for i, r in enumerate(responses):
            if r.status_code != 200:
                print(f"Request {i} failed: {r.status_code} {r.text}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
