import asyncio
import httpx
import time
import io
import sys
import os

from unittest.mock import MagicMock

# Mock google auth before anything else
import sys
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.cloud.storage'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()

# Add backend to sys.path so it can import its own modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

import main
from main import app, verify_token

# Mock dependencies
async def mock_verify_token():
    return "test-uid"

app.dependency_overrides[verify_token] = mock_verify_token

def mock_upload_to_gcs(path, name):
    return True

def mock_analyze_audio_file(path, local_data):
    return {"some": "data"}

def mock_strip_metadata(path):
    time.sleep(0.5) # Simulate blocking I/O

main.upload_to_gcs = mock_upload_to_gcs
main.analyze_audio_file = mock_analyze_audio_file
main.strip_metadata = mock_strip_metadata

async def run_benchmark():
    # To run test with AsyncClient directly against ASGI app
    # Requires httpx.ASGITransport
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.time()

        # Send N requests concurrently
        N = 5
        tasks = []
        for _ in range(N):
            files = {'file': ('test.mp3', io.BytesIO(b'dummy content'), 'audio/mpeg')}
            tasks.append(client.post("/api/analyze", files=files))

        responses = await asyncio.gather(*tasks)

        end = time.time()
        print(f"Total time for {N} requests: {end - start:.2f} seconds")
        for i, r in enumerate(responses):
            if r.status_code != 200:
                print(f"Request {i} failed: {r.status_code} {r.text}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
