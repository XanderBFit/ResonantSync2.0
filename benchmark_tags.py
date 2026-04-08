import asyncio
import httpx
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

import main
from main import app, verify_token

# Mock Firestore
mock_db = MagicMock()
main.db = mock_db

# Mock dependencies
async def mock_verify_token():
    return "test-uid"

app.dependency_overrides[verify_token] = mock_verify_token

# Mock download_from_gcs to simulate a slow download
def mock_download_from_gcs(blob_name, local_path):
    time.sleep(1.0) # Simulate 1 second download
    with open(local_path, "w") as f:
        f.write("fake mp3 content")
    return True

# Mock read_disco_metadata
def mock_read_disco_metadata(local_path):
    return {"TIT2": "Test Title", "TPE1": "Test Artist"}

main.download_from_gcs = mock_download_from_gcs
main.read_disco_metadata = mock_read_disco_metadata

async def run_benchmark():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("Running baseline benchmark for /api/tags/{file_id}...")

        # Scenario: 5 requests for the same file
        file_id = "test-file-id"

        start = time.time()
        tasks = [client.get(f"/api/tags/{file_id}") for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        end = time.time()

        print(f"Total time for 5 requests: {end - start:.2f} seconds")
        for i, r in enumerate(responses):
            if r.status_code != 200:
                print(f"Request {i} failed: {r.status_code} {r.text}")
            else:
                print(f"Request {i} succeeded: {r.json()}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
