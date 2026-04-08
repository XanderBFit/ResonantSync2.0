import asyncio
import time
import threading
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
import httpx
import os
import sys
from unittest.mock import MagicMock, patch

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Mock dependencies before importing main
mock_firestore = MagicMock()
mock_storage = MagicMock()
mock_firebase_admin = MagicMock()

with patch.dict(sys.modules, {
    'google.cloud.firestore': mock_firestore,
    'google.cloud.storage': mock_storage,
    'firebase_admin': mock_firebase_admin,
    'firebase_admin.auth': MagicMock(),
    'librosa': MagicMock(),
    'numpy': MagicMock(),
    'ffmpeg': MagicMock(),
    'metadata_manager': MagicMock(),
    'storage_manager': MagicMock()
}):
    import main
    from main import app, verify_token

# Mock dependency
async def mock_verify_token():
    return "test-uid"

app.dependency_overrides[verify_token] = mock_verify_token

# Mock the heavy operations in generate_promos
def mock_download_from_gcs(blob, path):
    return True

def mock_upload_to_gcs(path, blob):
    return True

def mock_librosa_load(path, **kwargs):
    time.sleep(2)  # Simulate heavy CPU work
    return MagicMock(), 44100

def mock_librosa_get_duration(**kwargs):
    return 120.0

def mock_librosa_feature_rms(**kwargs):
    return [MagicMock()]

def mock_read_disco_metadata(path):
    return {"TIT2": "Test Title", "TPE1": "Test Artist"}

main.download_from_gcs = mock_download_from_gcs
main.upload_to_gcs = mock_upload_to_gcs
main.librosa.load = mock_librosa_load
main.librosa.get_duration = mock_librosa_get_duration
main.librosa.feature.rms = mock_librosa_feature_rms
main.read_disco_metadata = mock_read_disco_metadata
main.ffmpeg.input().output().overwrite_output().run = MagicMock()

async def heartbeat():
    lags = []
    for _ in range(30):
        start = time.perf_counter()
        await asyncio.sleep(0.1)
        end = time.perf_counter()
        lag = end - start - 0.1
        lags.append(lag)
        # print(f"Heartbeat lag: {lag:.4f}s")
    return lags

async def run_benchmark():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("Starting heartbeat...")
        heartbeat_task = asyncio.create_task(heartbeat())

        await asyncio.sleep(0.5) # Let heartbeat stabilize

        print("Sending generate_promos request...")
        start_time = time.perf_counter()
        response = await client.post("/api/promos/test-file")
        end_time = time.perf_counter()

        print(f"Request took {end_time - start_time:.2f}s")
        print(f"Response status: {response.status_code}")

        lags = await heartbeat_task
        max_lag = max(lags)
        avg_lag = sum(lags) / len(lags)
        print(f"Max event loop lag: {max_lag:.4f}s")
        print(f"Avg event loop lag: {avg_lag:.4f}s")

        if max_lag > 1.0:
            print("FAILURE: Event loop was blocked!")
        else:
            print("SUCCESS: Event loop remained responsive.")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
