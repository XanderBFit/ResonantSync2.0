import sys
import time
import os
from unittest.mock import MagicMock

# Mocking dependencies to allow importing main.py without fastapi installed
class MockFastAPI:
    def __init__(self, *args, **kwargs): pass
    def add_middleware(self, *args, **kwargs): pass
    def mount(self, *args, **kwargs): pass
    def get(self, *args, **kwargs): return lambda x: x
    def post(self, *args, **kwargs): return lambda x: x
    def delete(self, *args, **kwargs): return lambda x: x

fastapi_mock = MagicMock()
fastapi_mock.FastAPI = MockFastAPI
fastapi_mock.Depends = lambda x: x
fastapi_mock.Form = lambda x=None, **kwargs: x
fastapi_mock.File = lambda x=None, **kwargs: x
fastapi_mock.Header = lambda x=None, **kwargs: x
fastapi_mock.HTTPException = Exception

sys.modules['fastapi'] = fastapi_mock
sys.modules['fastapi.middleware.cors'] = MagicMock()
sys.modules['fastapi.security'] = MagicMock()
sys.modules['fastapi.responses'] = MagicMock()
sys.modules['fastapi.staticfiles'] = MagicMock()

# Mock GCP and other libraries
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.cloud.storage'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.auth'] = MagicMock()
sys.modules['librosa'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['ffmpeg'] = MagicMock()
sys.modules['mutagen'] = MagicMock()
sys.modules['mutagen.mp3'] = MagicMock()
sys.modules['mutagen.id3'] = MagicMock()
sys.modules['pyloudnorm'] = MagicMock()
sys.modules['reportlab'] = MagicMock()
sys.modules['reportlab.lib'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'] = MagicMock()
sys.modules['reportlab.pdfgen'] = MagicMock()

# Add backend to path
sys.path.append(os.path.abspath('backend'))

import main

# Setup mock behavior for the benchmark
mock_db = MagicMock()
main.db = mock_db

def mock_download_from_gcs(blob_name, local_path):
    time.sleep(1.0) # Simulate 1 second download
    return True

def mock_read_disco_metadata(local_path):
    return {"TIT2": "Test Title", "TPE1": "Test Artist"}

main.download_from_gcs = mock_download_from_gcs
main.read_disco_metadata = mock_read_disco_metadata

async def run_benchmark(iterations=5, use_cache=False):
    file_id = "test-file-id"

    if use_cache:
        # Mock Firestore to return cached data
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"cachedTags": {"TIT2": "Cached Title", "TPE1": "Cached Artist"}}
        mock_db.collection().document().get.return_value = mock_doc
    else:
        # Mock Firestore to return nothing
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection().document().get.return_value = mock_doc

    print(f"Running benchmark (use_cache={use_cache})...")
    start = time.time()
    for i in range(iterations):
        await main.get_tags(file_id)
    end = time.time()

    avg_time = (end - start) / iterations
    print(f"Total time for {iterations} iterations: {end - start:.4f}s")
    print(f"Average time per request: {avg_time:.4f}s")
    return avg_time

if __name__ == "__main__":
    import asyncio

    async def main_bench():
        # Baseline
        baseline = await run_benchmark(use_cache=False)

        # We need to manually mock the behavior we WANT to implement to see the potential gain
        # because get_tags currently doesn't check the cache.

        # Save original
        original_get_tags = main.get_tags

        # Mock what the optimized version would do
        async def optimized_get_tags(file_id: str):
            doc = main.db.collection("processedTracks").document(file_id).get()
            if doc.exists:
                data = doc.to_dict()
                if "cachedTags" in data:
                    return data["cachedTags"]
            return await original_get_tags(file_id)

        main.get_tags = optimized_get_tags

        # Optimized
        optimized = await run_benchmark(use_cache=True)

        print(f"\nPotential improvement: {baseline - optimized:.4f}s per request ({(1 - optimized/baseline)*100:.2f}%)")

    asyncio.run(main_bench())
