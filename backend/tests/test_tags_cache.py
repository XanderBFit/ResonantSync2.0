import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Mock FastAPI and other dependencies before importing main
# We use the same strategy as in the benchmark to avoid environment issues
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
import asyncio

def test_get_tags_cache_hit():
    file_id = "test-file-id"
    cached_tags = {"TIT2": "Cached Title", "TPE1": "Cached Artist"}

    # Mock Firestore hit
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"cachedTags": cached_tags}

    with patch.object(main.db.collection("processedTracks"), 'document') as mock_doc_ref:
        mock_doc_ref.return_value.get.return_value = mock_doc

        # Mock download_from_gcs to ensure it's NOT called
        with patch('main.download_from_gcs') as mock_download:
            result = asyncio.run(main.get_tags(file_id))

            assert result == cached_tags
            mock_download.assert_not_called()

def test_get_tags_cache_miss_with_doc_update():
    file_id = "test-file-id"
    parsed_tags = {"TIT2": "Parsed Title", "TPE1": "Parsed Artist"}

    # Mock Firestore doc exists but no cachedTags
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {} # No cachedTags

    with patch.object(main.db.collection("processedTracks"), 'document') as mock_doc_ref:
        mock_doc_ref.return_value.get.return_value = mock_doc

        with patch('main.download_from_gcs', return_value=True):
            with patch('main.read_disco_metadata', return_value=parsed_tags):
                result = asyncio.run(main.get_tags(file_id))

                assert result == parsed_tags
                # Should have updated the cache
                mock_doc_ref.return_value.update.assert_called_with({"cachedTags": parsed_tags})

def test_get_tags_cache_miss_no_doc():
    file_id = "test-file-id"
    parsed_tags = {"TIT2": "Parsed Title", "TPE1": "Parsed Artist"}

    # Mock Firestore doc does not exist
    mock_doc = MagicMock()
    mock_doc.exists = False

    with patch.object(main.db.collection("processedTracks"), 'document') as mock_doc_ref:
        mock_doc_ref.return_value.get.return_value = mock_doc

        with patch('main.download_from_gcs', return_value=True):
            with patch('main.read_disco_metadata', return_value=parsed_tags):
                result = asyncio.run(main.get_tags(file_id))

                assert result == parsed_tags
                # Should NOT have updated anything
                mock_doc_ref.return_value.update.assert_not_called()
